from app.retrieval.text import tokenize

W_FUSION, W_NAME, W_CONTACT, W_PRICE = 0.6, 0.25, 0.1, 0.05


def heuristic_rerank(query: str, candidates: list[dict], max_price: int = 0) -> list[dict]:
    """candidates: [{'id','provider','fusion',...}] -> sắp xếp lại, thêm khóa 'score'."""
    if not candidates:
        return []
    top = max(c["fusion"] for c in candidates) or 1.0
    q_tokens = {t for t in tokenize(query) if "_" not in t}

    ranked = []
    for c in candidates:
        p = c["provider"]
        name_tokens = set(tokenize(p.get("provider_name", "")))
        name_hit = len(q_tokens & name_tokens) / len(q_tokens) if q_tokens else 0.0
        has_contact = 1.0 if p.get("phones") else 0.0
        prices = [x["price_min"] for x in p.get("pricing") or [] if x.get("price_min")]
        if max_price and prices:
            price_fit = 1.0 if min(prices) <= max_price else 0.0
        else:
            price_fit = 1.0 if prices else 0.0
        score = (
            W_FUSION * (c["fusion"] / top)
            + W_NAME * name_hit
            + W_CONTACT * has_contact
            + W_PRICE * price_fit
        )
        ranked.append({**c, "score": round(score, 4)})
    return sorted(ranked, key=lambda c: c["score"], reverse=True)