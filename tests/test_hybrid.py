from app.retrieval.embeddings import FakeEmbedder
from app.retrieval.hybrid import hybrid_search


def search(db, query, **kw):
    return hybrid_search(db, FakeEmbedder(), query, **kw)


def names(results):
    return [r["provider"]["provider_name"] for r in results]


def test_xep_dung_theo_noi_dung(indexed_db):
    assert names(search(indexed_db, "vệ sinh nhà theo giờ ở Thủ Đức"))[0] == "Vệ Sinh Nhà SG"
    assert names(search(indexed_db, "sửa điện nước tại nhà"))[0] == "Thợ Điện Nước 24h"


def test_khong_dau_van_tim_duoc(indexed_db):
    assert names(search(indexed_db, "sua dien nuoc tai nha"))[0] == "Thợ Điện Nước 24h"


def test_bo_loc_cung_duoc_ton_trong(indexed_db):
    res = search(indexed_db, "vệ sinh nhà", category="điện nước")
    assert names(res) == ["Thợ Điện Nước 24h"]


def test_danh_muc_khong_ton_tai(indexed_db):
    assert search(indexed_db, "gì đó", category="không có") == []


def test_loc_gia(indexed_db):
    assert names(search(indexed_db, "dọn dẹp", max_price=100000)) == ["Vệ Sinh Nhà SG"]


def test_ket_qua_co_thong_tin_xep_hang(indexed_db):
    top = search(indexed_db, "vệ sinh nhà theo giờ")[0]
    assert {"id", "provider", "fusion", "lex_rank", "sem_rank", "score"} <= set(top)
    assert top["lex_rank"] is not None and top["sem_rank"] is not None


def test_van_chay_khi_chua_co_vector(test_db):
    res = search(test_db, "sửa điện nước")  # chưa build_index
    assert names(res)[0] == "Thợ Điện Nước 24h"
    assert res[0]["sem_rank"] is None


def test_gioi_han_top_k(indexed_db):
    assert len(search(indexed_db, "nhà", top_k=2)) == 2