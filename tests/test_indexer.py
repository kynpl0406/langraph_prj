from app.retrieval.embeddings import FakeEmbedder
from app.retrieval.indexer import VECTORS, build_index


def test_index_lan_dau_va_lan_hai(test_db):
    assert build_index(test_db, FakeEmbedder()) == {
        "total": 3, "embedded": 3, "skipped": 0, "removed": 0,
    }
    assert test_db[VECTORS].count_documents({}) == 3

    r2 = build_index(test_db, FakeEmbedder())
    assert r2["embedded"] == 0 and r2["skipped"] == 3


def test_chi_embed_lai_ban_ghi_da_doi(test_db):
    build_index(test_db, FakeEmbedder())
    test_db.providers.update_one(
        {"provider_name": "Dọn Dẹp Xanh"}, {"$set": {"description": "Mô tả mới hoàn toàn"}}
    )
    assert build_index(test_db, FakeEmbedder())["embedded"] == 1


def test_xoa_vector_cua_provider_da_xoa(test_db):
    build_index(test_db, FakeEmbedder())
    test_db.providers.delete_one({"provider_name": "Dọn Dẹp Xanh"})
    assert build_index(test_db, FakeEmbedder())["removed"] == 1