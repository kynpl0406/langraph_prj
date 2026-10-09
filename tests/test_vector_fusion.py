from app.retrieval.fusion import rrf
from app.retrieval.vector import cosine_rank


def test_cosine_rank_xep_theo_do_giong():
    vecs = {"a": [1, 0], "b": [0.9, 0.1], "c": [0, 1]}
    assert [i for i, _ in cosine_rank([1, 0], vecs)] == ["a", "b", "c"]


def test_cosine_rank_rong():
    assert cosine_rank([1, 0], {}) == []


def test_rrf_muc_xuat_hien_o_ca_hai_kenh_thang():
    scores = rrf([["a", "b"], ["c", "b"]])
    assert max(scores, key=scores.get) == "b"


def test_rrf_trong_so():
    scores = rrf([["a"], ["b"]], weights=[1.0, 2.0])
    assert scores["b"] > scores["a"]