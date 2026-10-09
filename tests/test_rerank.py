from app.retrieval.rerank import heuristic_rerank


def cand(name, fusion, **extra):
    return {"id": name, "fusion": fusion, "provider": {"provider_name": name, **extra}}


def test_ten_khop_truy_van_co_the_vuot_diem_fusion_cao_hon():
    a = cand("Thợ ABC", 1.0)
    b = cand("Dọn Dẹp Xanh", 0.9)
    result = heuristic_rerank("xanh", [a, b])
    assert [c["id"] for c in result] == ["Dọn Dẹp Xanh", "Thợ ABC"]


def test_loc_gia_phat_nha_cung_cap_dat():
    cheap = cand("Rẻ", 1.0, pricing=[{"price_min": 80000}])
    pricey = cand("Đắt", 1.0, pricing=[{"price_min": 500000}])
    result = heuristic_rerank("dịch vụ", [pricey, cheap], max_price=100000)
    assert result[0]["id"] == "Rẻ"


def test_rong():
    assert heuristic_rerank("x", []) == []