import re


def rx(text: str) -> dict:
    """Regex không phân biệt hoa thường; re.escape để input không thành regex."""
    return {"$regex": re.escape(text), "$options": "i"}


def build_query(db, category: str = "", area: str = "", max_price: int = 0, keyword: str = ""):
    """Trả về filter Mongo, hoặc None nếu danh mục không tồn tại (chắc chắn không có kết quả)."""
    conds = []

    if category:
        cats = list(db.categories.find(
            {"$or": [
                {"code": rx(category)},
                {"name.vi": rx(category)},
                {"name.en": rx(category)},
                {"aliases": rx(category)},
            ]},
            {"code": 1},
        ))
        if not cats:
            return None
        conds.append({"category_codes": {"$in": [c["code"] for c in cats]}})

    if keyword:
        conds.append({"$or": [
            {"provider_name": rx(keyword)},
            {"description": rx(keyword)},
        ]})

    if area:
        conds.append({"$or": [
            {"service_coverage.raw_text": rx(area)},
            {"location.address_line": rx(area)},
            {"location.ward.name": rx(area)},
            {"location.district.name": rx(area)},
            {"location.province.name": rx(area)},
            {"description": rx(area)},
        ]})

    if max_price:
        conds.append({"pricing": {"$elemMatch": {"price_min": {"$lte": max_price}}}})

    return {"$and": conds} if conds else {}