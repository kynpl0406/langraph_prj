import hashlib
import math
from functools import lru_cache

from app.retrieval.text import tokenize

EMBED_MODEL = "models/gemini-embedding-001"


class FakeEmbedder:
    """Embedding giả cho test: băm từ vào vector, từ trùng nhau thì vector gần nhau."""

    model = "fake-hash-64"

    def __init__(self, dim: int = 64):
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in tokenize(text):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vec(text)


@lru_cache(maxsize=1)
def get_embedder():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    return GoogleGenerativeAIEmbeddings(model=EMBED_MODEL)