import re

from langchain_core.tools import tool

from app.db import db, to_plain

LIMIT = 8  # luôn giới hạn kết quả để không tràn context của Gemini


def _rx(text: str) -> dict:
    """Regex không phân biệt hoa thường. re.escape để input người dùng không thành regex."""
    return {"$regex": re.escape(text), "$options": "i"}


def _slim(p: dict) -> dict:
    """Rút gọn 1 provider để agent không phải đọc quá nhiều chữ."""
    p["description"] = (p.get("description") or "")[:250]
    p["pricing"] = (p.get("pricing") or [])[:5]
    p["phones"] = [x.get("raw") for x in (p.get("phones") or [])][:2]
    return p


@tool
def list_categories() -> list:
    """Liệt kê tất cả danh mục dịch vụ (mã, tên tiếng Việt/Anh, từ đồng nghĩa).
    Gọi tool này trước khi tìm nhà cung cấp nếu chưa rõ danh mục."""
    return to_plain(list(db.categories.find({}, {"code": 1, "name": 1, "aliases": 1})))


@tool
def search_providers(
    keyword: str = "", category: str = "", area: str = "", max_price: int = 0
) -> list:
    """Tìm nhà cung cấp dịch vụ gia đình. Có thể truyền một, vài hoặc tất cả tham số.
    keyword: từ khóa trong tên hoặc mô tả (tiếng Việt có dấu).
    category: tên hoặc mã danh mục, ví dụ 'điện nước', 'vệ sinh', 'sofa'.
    area: quận, phường hoặc thành phố, ví dụ 'Thủ Đức', 'Quận 9'.
    max_price: giá tối thiểu của dịch vụ không vượt quá mức này (VND), 0 là không giới hạn.
    Lưu ý: dữ liệu chưa được kiểm duyệt, một số dịch vụ chỉ báo giá theo yêu cầu."""
    conds = []

    if category:
        cats = list(
            db.categories.find(
                {
                    "$or": [
                        {"code": _rx(category)},
                        {"name.vi": _rx(category)},
                        {"name.en": _rx(category)},
                        {"aliases": _rx(category)},
                    ]
                },
                {"code": 1},
            )
        )
        if not cats:
            return []
        conds.append({"category_codes": {"$in": [c["code"] for c in cats]}})

    if keyword:
        conds.append(
            {
                "$or": [
                    {"provider_name": _rx(keyword)},
                    {"description": _rx(keyword)},
                ]
            }
        )

    if area:
        conds.append(
            {
                "$or": [
                    {"service_coverage.raw_text": _rx(area)},
                    {"location.address_line": _rx(area)},
                    {"location.ward.name": _rx(area)},
                    {"location.district.name": _rx(area)},
                    {"location.province.name": _rx(area)},
                    {"description": _rx(area)},
                ]
            }
        )

    if max_price:
        conds.append({"pricing": {"$elemMatch": {"price_min": {"$lte": max_price}}}})

    q = {"$and": conds} if conds else {}
    projection = {
        "provider_name": 1,
        "description": 1,
        "category_codes": 1,
        "pricing": 1,
        "phones": 1,
        "service_coverage.raw_text": 1,
        "location.address_line": 1,
        "location.district.name": 1,
        "canonical_url": 1,
        "provider_status": 1,
    }
    docs = db.providers.find(q, projection).limit(LIMIT)
    return to_plain([_slim(d) for d in docs])


@tool
def get_provider_detail(provider_name: str) -> dict:
    """Xem chi tiết một nhà cung cấp (bảng giá đầy đủ, địa chỉ, liên hệ) theo tên."""
    doc = db.providers.find_one(
        {"provider_name": _rx(provider_name)},
        {"evidences": 0, "review": 0},
    )
    return to_plain(doc) if doc else {"error": "Không tìm thấy nhà cung cấp"}


ALL_TOOLS = [list_categories, search_providers, get_provider_detail]
