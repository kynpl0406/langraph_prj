import numpy as np


def cosine_rank(query_vec, vectors: dict[str, list[float]], top_n: int = 20):
    """Trả về [(id, độ giống)] giảm dần."""
    if not vectors:
        return []
    ids = list(vectors)
    m = np.array([vectors[i] for i in ids], dtype=float)
    q = np.array(query_vec, dtype=float)
    norms = np.linalg.norm(m, axis=1) * np.linalg.norm(q)
    sims = (m @ q) / np.where(norms == 0, 1, norms)
    order = np.argsort(-sims)[:top_n]
    return [(ids[i], float(sims[i])) for i in order]