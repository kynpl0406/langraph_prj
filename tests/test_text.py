from app.retrieval.text import load_category_names, normalize, provider_to_text, tokenize


def test_normalize_bo_dau_va_chu_d():
    assert normalize("Thủ Đức") == "thu duc"


def test_tokenize_co_bigram():
    assert {"ve", "sinh", "nha", "ve_sinh", "sinh_nha"} <= set(tokenize("Vệ sinh nhà"))


def test_provider_to_text_gom_cac_field():
    p = {
        "provider_name": "ABC",
        "description": "mô tả",
        "category_codes": ["ve_sinh"],
        "service_coverage": {"raw_text": "Quận 7"},
        "pricing": [{"label": "Theo giờ"}],
    }
    text = provider_to_text(p, {"ve_sinh": "Vệ sinh dọn nhà"})
    for part in ["ABC", "mô tả", "dọn nhà", "Quận 7", "Theo giờ"]:
        assert part in text


def test_load_category_names(test_db):
    assert "dọn nhà" in load_category_names(test_db)["ve_sinh"]