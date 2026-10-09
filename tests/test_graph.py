import uuid

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph import build_graph
from app.nodes import Understanding, recent, to_text
from app.retrieval.embeddings import FakeEmbedder


class FakeUnderstander:
    """Thay Gemini ở bước understand: trả Understanding theo kịch bản."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.results.pop(0)


class FakeLLM:
    """Thay Gemini ở bước generate/chitchat."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return self.responses.pop(0)


@pytest.fixture
def env(indexed_db, monkeypatch):
    monkeypatch.setattr("app.nodes.get_embedder", lambda: FakeEmbedder())
    return indexed_db


def run(graph, text, thread=None):
    cfg = {"configurable": {"thread_id": thread or uuid.uuid4().hex}}
    return graph.invoke({"messages": [("user", text)]}, cfg)


def test_luong_search_day_du(env, monkeypatch):
    und = FakeUnderstander(
        Understanding(intent="search", query="vệ sinh nhà theo giờ", area="Thủ Đức")
    )
    llm = FakeLLM(AIMessage(content="Có Vệ Sinh Nhà SG [1]."))
    monkeypatch.setattr("app.nodes.understander", und)
    monkeypatch.setattr("app.nodes.llm", llm)

    result = run(build_graph(MemorySaver()), "Tìm dịch vụ vệ sinh nhà ở Thủ Đức")

    assert to_text(result["messages"][-1].content) == "Có Vệ Sinh Nhà SG [1]."
    assert [s["name"] for s in result["sources"]] == ["Vệ Sinh Nhà SG"]
    system = llm.calls[0][0].content
    assert "NGỮ CẢNH" in system and "[1] Vệ Sinh Nhà SG" in system
    log = env.agent_query_logs.find_one()
    assert log["rewritten_query"] == "vệ sinh nhà theo giờ"
    assert log["sources"] == ["Vệ Sinh Nhà SG"]


def test_tu_noi_long_bo_loc_khi_khong_co_ket_qua(env, monkeypatch):
    und = FakeUnderstander(Understanding(intent="search", query="vệ sinh nhà", area="Quận 99"))
    llm = FakeLLM(AIMessage(content="ok"))
    monkeypatch.setattr("app.nodes.understander", und)
    monkeypatch.setattr("app.nodes.llm", llm)

    result = run(build_graph(MemorySaver()), "Vệ sinh nhà ở Quận 99")

    assert result["relaxed"] == ["area"]
    assert result["attempt"] == 2
    assert result["sources"]
    assert "khu vực" in llm.calls[0][0].content


def test_khong_co_du_lieu_van_tra_loi(env, monkeypatch):
    env.providers.delete_many({})
    und = FakeUnderstander(
        Understanding(intent="search", query="vệ sinh nhà", category="vệ sinh")
    )
    llm = FakeLLM(AIMessage(content="Không tìm thấy."))
    monkeypatch.setattr("app.nodes.understander", und)
    monkeypatch.setattr("app.nodes.llm", llm)

    result = run(build_graph(MemorySaver()), "Vệ sinh nhà")

    assert result["relaxed"] == ["category"]
    assert result["sources"] == []
    assert "(không tìm thấy nhà cung cấp phù hợp)" in llm.calls[0][0].content


def test_chitchat_khong_truy_xuat(env, monkeypatch):
    und = FakeUnderstander(Understanding(intent="chitchat", query="xin chào"))
    llm = FakeLLM(AIMessage(content="Xin chào!"))
    monkeypatch.setattr("app.nodes.understander", und)
    monkeypatch.setattr("app.nodes.llm", llm)

    result = run(build_graph(MemorySaver()), "Chào bạn")

    assert result["sources"] == []
    assert len(llm.calls) == 1
    assert to_text(result["messages"][-1].content) == "Xin chào!"


def test_nho_ngu_canh_giua_cac_luot(env, monkeypatch):
    und = FakeUnderstander(
        Understanding(intent="search", query="vệ sinh nhà", area="Thủ Đức"),
        Understanding(intent="search", query="sửa điện nước", area="Quận 7"),
    )
    llm = FakeLLM(AIMessage(content="Trả lời 1"), AIMessage(content="Trả lời 2"))
    monkeypatch.setattr("app.nodes.understander", und)
    monkeypatch.setattr("app.nodes.llm", llm)

    graph = build_graph(MemorySaver())
    run(graph, "Tìm vệ sinh nhà ở Thủ Đức", "cung-phien")
    run(graph, "Còn điện nước ở Quận 7?", "cung-phien")

    assert [m.type for m in und.calls[1]] == ["system", "human", "ai", "human"]


def test_loi_ghi_log_khong_lam_sap_agent(env, monkeypatch, capsys):
    class BrokenCollection:
        def insert_one(self, doc):
            raise RuntimeError("không có quyền ghi")

    class BrokenDB:
        agent_query_logs = BrokenCollection()

    monkeypatch.setattr(
        "app.nodes.understander", FakeUnderstander(Understanding(intent="chitchat", query="hi"))
    )
    monkeypatch.setattr("app.nodes.llm", FakeLLM(AIMessage(content="Chào bạn")))
    monkeypatch.setattr("app.nodes.db", BrokenDB())

    result = run(build_graph(MemorySaver()), "hi")

    assert to_text(result["messages"][-1].content) == "Chào bạn"
    assert "Không ghi được log" in capsys.readouterr().out


def test_recent_bo_tin_nhan_ai_o_dau():
    msgs = [HumanMessage("a"), AIMessage("b"), HumanMessage("c")]
    assert [m.content for m in recent(msgs, n=2)] == ["c"]


def test_to_text_xu_ly_content_dang_list():
    assert to_text("abc") == "abc"
    assert to_text([{"type": "text", "text": "xin "}, {"type": "text", "text": "chào"}]) == "xin chào"