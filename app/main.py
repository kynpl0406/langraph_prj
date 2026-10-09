from app.graph import app
from app.nodes import to_text


def ask(question: str):
    print(f"\n👤 {question}")
    for step in app.stream({"messages": [("user", question)]}, stream_mode="updates"):
        for node, out in step.items():
            for m in (out or {}).get("messages", []):
                if m.type == "ai" and m.tool_calls:
                    calls = [(t["name"], t["args"]) for t in m.tool_calls]
                    print(f"🧠 [{node}] quyết định gọi tool: {calls}")
                elif m.type == "tool":
                    print(f"🔧 [{node}] kết quả: {to_text(m.content)[:200]}")
                elif m.type == "ai":
                    print(f"🤖 [{node}] {to_text(m.content)}")
            if node == "logger":
                print("📝 [logger] đã ghi vào query_logs")


if __name__ == "__main__":
    print("Gõ câu hỏi (gõ 'exit' để thoát)")
    while True:
        q = input("\n> ").strip()
        if q.lower() in {"exit", "quit", ""}:
            break
        try:
            ask(q)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(
                    "⏳ Hết quota Gemini miễn phí (khoảng 5 request/phút). Đợi 1 phút rồi hỏi lại."
                )
            else:
                raise
