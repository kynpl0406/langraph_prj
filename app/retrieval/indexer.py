import hashlib
from datetime import datetime, timezone

from app.retrieval.text import load_category_names, provider_to_text

VECTORS = "provider_vectors"


def build_index(db, embedder) -> dict:
    cat_names = load_category_names(db)
    model = getattr(embedder, "model", "unknown")
    existing = {
        v["provider_id"]: v.get("text_hash")
        for v in db[VECTORS].find({}, {"provider_id": 1, "text_hash": 1})
    }

    all_ids, todo = [], []
    for p in db.providers.find({}, {"evidences": 0}):
        pid = str(p["_id"])
        all_ids.append(pid)
        text = provider_to_text(p, cat_names)
        digest = hashlib.sha256(f"{model}|{text}".encode()).hexdigest()
        if existing.get(pid) != digest:
            todo.append((pid, text, digest))

    if todo:
        vectors = embedder.embed_documents([t[1] for t in todo])
        now = datetime.now(timezone.utc)
        for (pid, _, digest), vec in zip(todo, vectors):
            db[VECTORS].update_one(
                {"provider_id": pid},
                {"$set": {"provider_id": pid, "text_hash": digest, "model": model,
                          "embedding": vec, "updated_at": now}},
                upsert=True,
            )

    removed = db[VECTORS].delete_many({"provider_id": {"$nin": all_ids}}).deleted_count
    return {"total": len(all_ids), "embedded": len(todo),
            "skipped": len(all_ids) - len(todo), "removed": removed}


if __name__ == "__main__":
    from app.db import db
    from app.retrieval.embeddings import get_embedder

    print(build_index(db, get_embedder()))