from collections import defaultdict


def rrf(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None):
    """rankings: mỗi phần tử là danh sách id đã xếp hạng của một kênh."""
    weights = weights or [1.0] * len(rankings)
    scores: dict[str, float] = defaultdict(float)
    for w, ranking in zip(weights, rankings):
        for rank, item in enumerate(ranking, start=1):
            scores[item] += w / (k + rank)
    return dict(scores)