import uuid

from app.graph import app
from app.nodes import to_text


def ask(question: str, config: dict):
    print(f"\n👤 {question}")
    sources = []
    for step in app.stream({"messages": [("user", question)]}, config, stream_mode="updates"):
        for node, out in step.items():
            out = out or {}
            if node == "understand":
                print(f"🧭 [understand] intent={out['intent']} | query='{out['query']}' | "
                      f"category='{out['category']}' area='{out['area']}' max_price={out['max_price']}")
            elif node == "retrieve":
                sources = out["sources"]
                print(f"🔎 [retrieve] lần {out['attempt']}: {len(sources)} nguồn")
                for t in out["trace"]:
                    print(f"     - {t['name']}  score={t['score']}  "
                          f"bm25#{t['lex'] or '-'}  vector#{t['sem'] or '-'}")
            elif node == "relax":
                print(f"🪜 [relax] không có kết quả, bỏ bộ lọc: {out['relaxed'][-1]}")
            elif node in ("generate", "chitchat"):
                print(f"🤖 {to_text(out['messages'][-1].content)}")
                if sources:
                    print("📚 Nguồn: " + " | ".join(f"[{s['n']}] {s['name']}" for s in sources))
            elif node == "logger":
                print("📝 [logger] đã ghi agent_query_logs")


if __name__ == "__main__":
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    print("Gõ câu hỏi (gõ 'exit' để thoát). Agent nhớ ngữ cảnh trong phiên này.")
    while True:
        q = input("\n> ").strip()
        if q.lower() in {"exit", "quit", ""}:
            break
        try:
            ask(q, config)
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print("⏳ Hết quota Gemini miễn phí (khoảng 5 request/phút). Đợi 1 phút rồi hỏi lại.")
            else:
                raise