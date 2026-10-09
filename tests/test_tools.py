import json

from app.tools import LIMIT, get_provider_detail, list_categories, search_providers


def names(result):
    return {p["provider_name"] for p in result}


def test_list_categories(test_db):
    result = list_categories.invoke({})
    assert {c["code"] for c in result} == {"dien_nuoc", "ve_sinh", "house_cleaning"}


def test_tim_theo_ten_danh_muc_tieng_viet(test_db):
    result = search_providers.invoke({"category": "điện nước"})
    assert names(result) == {"Thợ Điện Nước 24h"}


def test_tim_theo_alias_danh_muc(test_db):
    # alias "dọn nhà" thuộc danh mục ve_sinh -> 2 nhà cung cấp có mã ve_sinh
    result = search_providers.invoke({"category": "dọn nhà"})
    assert names(result) == {"Vệ Sinh Nhà SG", "Dọn Dẹp Xanh"}


def test_danh_muc_khong_ton_tai(test_db):
    assert search_providers.invoke({"category": "không có danh mục này"}) == []


def test_tim_theo_quan(test_db):
    result = search_providers.invoke({"area": "Thủ Đức"})
    assert names(result) == {"Vệ Sinh Nhà SG"}


def test_tim_khu_vuc_chi_xuat_hien_trong_mo_ta(test_db):
    # "Quận 9" chỉ nằm trong description của Vệ Sinh Nhà SG
    result = search_providers.invoke({"area": "quận 9"})
    assert names(result) == {"Vệ Sinh Nhà SG"}


def test_tu_khoa_khong_phan_biet_hoa_thuong(test_db):
    result = search_providers.invoke({"keyword": "XANH"})
    assert names(result) == {"Dọn Dẹp Xanh"}


def test_tu_khoa_la_regex_duoc_escape(test_db):
    # nếu không escape thì ".*" sẽ khớp mọi thứ
    assert search_providers.invoke({"keyword": ".*"}) == []


def test_loc_theo_gia_toi_da(test_db):
    # chỉ Vệ Sinh Nhà SG có mức giá khởi điểm <= 100000
    result = search_providers.invoke({"max_price": 100000})
    assert names(result) == {"Vệ Sinh Nhà SG"}


def test_ket_hop_danh_muc_va_gia(test_db):
    result = search_providers.invoke({"category": "vệ sinh", "max_price": 100000})
    assert names(result) == {"Vệ Sinh Nhà SG"}


def test_gioi_han_so_ket_qua(test_db):
    test_db.providers.insert_many(
        [{"provider_name": f"Dịch vụ {i}", "category_codes": ["ve_sinh"]} for i in range(12)]
    )
    result = search_providers.invoke({"category": "vệ sinh"})
    assert len(result) == LIMIT


def test_ket_qua_duoc_rut_gon(test_db):
    test_db.providers.insert_one(
        {
            "provider_name": "Nhà cung cấp dài dòng",
            "description": "x" * 1000,
            "category_codes": ["dien_nuoc"],
            "pricing": [
                {"label": f"gói {i}", "pricing_type": "fixed", "price_min": i} for i in range(10)
            ],
        }
    )
    result = search_providers.invoke({"keyword": "dài dòng"})
    p = result[0]
    assert len(p["description"]) <= 250
    assert len(p["pricing"]) <= 5

    vs = search_providers.invoke({"keyword": "Vệ Sinh Nhà SG"})[0]
    assert vs["phones"] == ["0767 448 555", "0767 224 555"]  # chỉ số raw, tối đa 2


def test_chi_tiet_nha_cung_cap(test_db):
    result = get_provider_detail.invoke({"provider_name": "vệ sinh nhà sg"})
    assert result["provider_name"] == "Vệ Sinh Nhà SG"
    assert len(result["pricing"]) == 3
    assert "evidences" not in result and "review" not in result
    json.dumps(result)  # ObjectId và datetime đã được đổi sang chuỗi


def test_chi_tiet_khong_tim_thay(test_db):
    assert "error" in get_provider_detail.invoke({"provider_name": "không tồn tại"})
