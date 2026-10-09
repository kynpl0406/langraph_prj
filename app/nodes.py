from datetime import datetime, timezone

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import MODEL_NAME
from app.db import db
from app.state import State
from app.tools import ALL_TOOLS

llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0)
llm_with_tools = llm.bind_tools(ALL_TOOLS)

SYSTEM = SystemMessage(
    content=(
        "Bạn là trợ lý tìm dịch vụ gia đình (điện nước, vệ sinh, sửa chữa...) tại Việt Nam. "
        "Luôn dùng tool để tra dữ liệu thật, không được bịa nhà cung cấp, giá hay số điện thoại. "
        "Nếu không có dữ liệu thì nói rõ là không tìm thấy. "
        "Cách đọc giá: pricing_type 'fixed' là giá cố định (price_min), 'range' là khoảng giá "
        "(price_min đến price_max), 'quote_based' là báo giá theo yêu cầu, không có số cụ thể. "
        "price_unit 'per_hour' nghĩa là tính theo giờ. "
        "Thông tin nhà cung cấp chưa được kiểm duyệt, hãy nhắc người dùng xác nhận lại "
        "với nhà cung cấp trước khi đặt. Trả lời ngắn gọn bằng tiếng Việt."
    )
)


def to_text(content) -> str:
    """Gemini đôi khi trả content dạng list các block, hàm này đưa về str."""
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if isinstance(b, dict))


def agent_node(state: State):
    reply = llm_with_tools.invoke([SYSTEM] + state["messages"])
    return {"messages": [reply]}


def logger_node(state: State):
    msgs = state["messages"]
    question = to_text(next(m for m in msgs if m.type == "human").content)
    tools_used = [tc["name"] for m in msgs if m.type == "ai" for tc in m.tool_calls]
    answer = to_text(msgs[-1].content)

    try:
        db.agent_query_logs.insert_one(
            {
                "question": question,
                "tools_used": tools_used,
                "answer": answer,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception as e:
        print(f"⚠️  Không ghi được log (có thể user Atlas chỉ có quyền đọc): {type(e).__name__}")
    return {}
