import math
from collections import Counter


class BM25:
    def __init__(self, docs_tokens: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.docs = docs_tokens
        self.k1, self.b = k1, b
        self.n = len(docs_tokens)
        self.avgdl = sum(len(d) for d in docs_tokens) / self.n if self.n else 0.0
        self.tf = [Counter(d) for d in docs_tokens]
        self.df = Counter()
        for d in docs_tokens:
            self.df.update(set(d))
            
    def idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        return math.log(1 + (self.n - n + 0.5) / (n + 0.5))
    
    def scores(self, query_tokens: list[str]) -> list[float]:
        out = [0.0] * self.n
        for i, (tf, doc) in enumerate(zip(self.tf, self.docs)):
            norm = 1 - self.b + self.b * len(doc) / (self.avgdl or 1.0)
            for term in set(query_tokens):
                f = tf.get(term, 0)
                if f:
                    out[i] += self.idf(term) * f * (self.k1 + 1) / (f + self.k1 * norm)
        return out
        
        