from app.retrieval.bm25 import BM25
from app.retrieval.filters import build_query
from app.retrieval.fusion import rrf
from app.retrieval.indexer import VECTORS
from app.retrieval.rerank import heuristic_rerank
from app.retrieval.text import load_category_names, provider_to_text, tokenize
from app.retrieval.vector import cosine_rank

POOL = 20  # số ứng viên giữ lại ở mỗi kênh


def hybrid_search(
    db, embedder, query: str, *, category: str = "", area: str = "",
    max_price: int = 0, top_k: int = 5, reranker=heuristic_rerank,
) -> list[dict]:
    # 1) Bộ lọc cứng: những provider được phép xuất hiện
    mongo_q = build_query(db, category=category, area=area, max_price=max_price)
    if mongo_q is None:
        return []
    allowed = {str(d["_id"]) for d in db.providers.find(mongo_q, {"_id": 1})}
    if not allowed:
        return []

    # 2) Corpus (21 bản ghi thì nạp hết; dữ liệu lớn hơn nên chuyển sang Atlas Search)
    cat_names = load_category_names(db)
    corpus = list(db.providers.find({}, {"evidences": 0}))
    ids = [str(p["_id"]) for p in corpus]
    by_id = dict(zip(ids, corpus))

    # 3) Kênh từ khóa
    bm25 = BM25([tokenize(provider_to_text(p, cat_names)) for p in corpus])
    scores = bm25.scores(tokenize(query))
    lexical = [
        i for i, s in sorted(zip(ids, scores), key=lambda x: -x[1]) if s > 0 and i in allowed
    ][:POOL]

    # 4) Kênh ngữ nghĩa (provider chưa được index thì kênh này bỏ qua nó)
    vecs = {
        v["provider_id"]: v["embedding"]
        for v in db[VECTORS].find({"provider_id": {"$in": list(allowed)}})
    }
    semantic = [i for i, _ in cosine_rank(embedder.embed_query(query), vecs, top_n=POOL)]

    # 5) Trộn kênh bằng RRF; nếu cả hai kênh đều rỗng thì lấy theo bộ lọc
    fused = rrf([lexical, semantic]) or {i: 0.0 for i in allowed}
    lex_rank = {i: r for r, i in enumerate(lexical, 1)}
    sem_rank = {i: r for r, i in enumerate(semantic, 1)}

    candidates = [
        {"id": i, "provider": by_id[i], "fusion": f,
         "lex_rank": lex_rank.get(i), "sem_rank": sem_rank.get(i)}
        for i, f in sorted(fused.items(), key=lambda x: -x[1])[:POOL]
    ]

    # 6) Rerank rồi cắt top_k
    return reranker(query, candidates, max_price=max_price)[:top_k]