from app.retrieval.text import normalize

UNIT = {
    "per_hour": "giờ", "per_visit": "lượt", "per_day": "ngày",
    "per_month": "tháng", "per_m2": "m²", "per_item": "cái",
}


def money(n) -> str:
    return f"{int(n):,}".replace(",", ".") + "đ"


def format_price(item: dict) -> str:
    label = item.get("label", "Dịch vụ")
    unit = UNIT.get(item.get("price_unit"), item.get("price_unit"))
    suffix = f"/{unit}" if unit else ""
    lo, hi = item.get("price_min"), item.get("price_max")
    if lo and hi:
        amount = f"{money(lo)}–{money(hi)}{suffix}"
    elif lo and item.get("pricing_type") == "fixed":
        amount = f"{money(lo)}{suffix}"
    elif lo:
        amount = f"từ {money(lo)}{suffix}"
    elif hi:
        amount = f"tối đa {money(hi)}{suffix}"
    else:
        amount = "báo giá theo yêu cầu"
    return f"{label}: {amount}"


def format_provider(idx: int, p: dict, desc_chars: int = 220) -> str:
    status = "" if p.get("provider_status") == "approved" else " (chưa kiểm duyệt)"
    loc = p.get("location") or {}
    area = (p.get("service_coverage") or {}).get("raw_text")
    lines = [f"[{idx}] {p.get('provider_name', 'Không rõ tên')}{status}"]
    if area:
        lines.append(f"Khu vực: {area}")
    if loc.get("address_line"):
        lines.append(f"Địa chỉ: {loc['address_line']}")
    prices = [format_price(x) for x in (p.get("pricing") or [])[:5]]
    if prices:
        lines.append("Giá: " + "; ".join(prices))
    phones = [x.get("raw") for x in (p.get("phones") or []) if x.get("raw")][:2]
    if phones:
        lines.append("Liên hệ: " + ", ".join(phones))
    if p.get("description"):
        lines.append("Mô tả: " + p["description"][:desc_chars])
    if p.get("canonical_url"):
        lines.append("Nguồn: " + p["canonical_url"])
    return "\n".join(lines)


def dedupe(providers: list[dict]) -> list[dict]:
    """Dữ liệu cào từ web hay trùng tên; giữ bản đứng trước (xếp hạng cao hơn)."""
    seen, out = set(), []
    for p in providers:
        key = normalize(p.get("provider_name", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def build_context(providers: list[dict], max_chars: int = 3500, max_items: int = 5):
    """Trả về (text context, danh sách provider đã dùng) theo đúng thứ tự đánh số."""
    blocks, used, total = [], [], 0
    for p in dedupe(providers):
        if len(used) >= max_items:
            break
        block = format_provider(len(used) + 1, p)
        if blocks and total + len(block) > max_chars:
            break
        blocks.append(block)
        used.append(p)
        total += len(block)
    return "\n\n".join(blocks), used