from langchain_core.messages import AIMessage

from app.graph import app
from app.nodes import to_text


class FakeLLM:
    """LLM giả: mỗi lần invoke trả phản hồi kế tiếp trong kịch bản, và ghi lại input."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0)


def test_agent_goi_tool_that_roi_tra_loi_va_ghi_log(test_db, monkeypatch):
    fake = FakeLLM(
        AIMessage(
            content="",
            tool_calls=[{"name": "search_providers", "args": {"area": "Thủ Đức"}, "id": "call_1"}],
        ),
        AIMessage(content="Có Vệ Sinh Nhà SG ở Thủ Đức."),
    )
    monkeypatch.setattr("app.nodes.llm_with_tools", fake)

    result = app.invoke({"messages": [("user", "Tìm dịch vụ ở Thủ Đức")]})

    # câu trả lời cuối là của LLM giả
    assert result["messages"][-1].content == "Có Vệ Sinh Nhà SG ở Thủ Đức."
    # tool thật đã chạy trên Mongo test
    tool_msgs = [m for m in result["messages"] if m.type == "tool"]
    assert len(tool_msgs) == 1
    assert "house_cleaning" in tool_msgs[0].content
    # LLM được gọi đúng 2 lần: một lần chọn tool, một lần đọc kết quả
    assert len(fake.calls) == 2
    # logger đã ghi log
    log = test_db.agent_query_logs.find_one()
    assert log["question"] == "Tìm dịch vụ ở Thủ Đức"
    assert log["tools_used"] == ["search_providers"]
    assert log["answer"] == "Có Vệ Sinh Nhà SG ở Thủ Đức."


def test_agent_tra_loi_thang_khong_dung_tool(test_db, monkeypatch):
    monkeypatch.setattr("app.nodes.llm_with_tools", FakeLLM(AIMessage(content="Xin chào!")))

    result = app.invoke({"messages": [("user", "Chào bạn")]})

    assert result["messages"][-1].content == "Xin chào!"
    assert test_db.agent_query_logs.find_one()["tools_used"] == []


def test_system_prompt_duoc_gui_cho_llm(test_db, monkeypatch):
    fake = FakeLLM(AIMessage(content="ok"))
    monkeypatch.setattr("app.nodes.llm_with_tools", fake)

    app.invoke({"messages": [("user", "hi")]})

    system_msg = fake.calls[0][0]
    assert system_msg.type == "system"
    assert "kiểm duyệt" in system_msg.content


def test_loi_ghi_log_khong_lam_sap_agent(test_db, monkeypatch, capsys):
    class BrokenCollection:
        def insert_one(self, doc):
            raise RuntimeError("không có quyền ghi")

    class BrokenDB:
        agent_query_logs = BrokenCollection()

    monkeypatch.setattr("app.nodes.llm_with_tools", FakeLLM(AIMessage(content="Vẫn trả lời được")))
    monkeypatch.setattr("app.nodes.db", BrokenDB())

    result = app.invoke({"messages": [("user", "hi")]})

    assert result["messages"][-1].content == "Vẫn trả lời được"
    assert "Không ghi được log" in capsys.readouterr().out


def test_to_text_xu_ly_content_dang_list():
    assert to_text("abc") == "abc"
    assert (
        to_text([{"type": "text", "text": "xin "}, {"type": "text", "text": "chào"}]) == "xin chào"
    )
