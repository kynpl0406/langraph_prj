from app.retrieval.context import build_context, format_price


def test_gia_co_dinh():
    item = {"label": "Dọn nhà", "pricing_type": "fixed", "price_min": 95000, "price_unit": "per_hour"}
    assert format_price(item) == "Dọn nhà: 95.000đ/giờ"


def test_gia_khoang():
    item = {"label": "Định kỳ", "pricing_type": "range", "price_min": 70000,
            "price_max": 85000, "price_unit": "per_hour"}
    assert format_price(item) == "Định kỳ: 70.000đ–85.000đ/giờ"


def test_bao_gia():
    item = {"label": "Giúp việc", "pricing_type": "quote_based"}
    assert format_price(item) == "Giúp việc: báo giá theo yêu cầu"


def test_loai_trung_danh_so_va_nhan_chua_kiem_duyet():
    a = {"provider_name": "Vệ Sinh Nhà SG", "provider_status": "pending_review"}
    b = {"provider_name": "vệ sinh nhà sg"}
    c = {"provider_name": "Dọn Dẹp Xanh"}
    text, used = build_context([a, b, c])
    assert len(used) == 2
    assert "[1] Vệ Sinh Nhà SG (chưa kiểm duyệt)" in text
    assert "[2] Dọn Dẹp Xanh" in text


def test_gioi_han_so_muc_va_do_dai():
    many = [{"provider_name": f"NCC {i}", "description": "x" * 200} for i in range(10)]
    assert len(build_context(many, max_items=3)[1]) == 3
    text, used = build_context(many, max_chars=500)
    assert 1 <= len(used) < 5
    assert len(text) <= 520