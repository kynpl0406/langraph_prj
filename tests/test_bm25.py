from app.retrieval.bm25 import BM25

DOCS = [["ve", "sinh", "nha"], ["dien", "nuoc", "nha"], ["sofa", "nem"]]


def test_doc_chua_tu_khoa_xep_dau():
    s = BM25(DOCS).scores(["dien"])
    assert s.index(max(s)) == 1
    assert s[0] == 0 and s[2] == 0


def test_tu_hiem_co_trong_so_cao_hon_tu_pho_bien():
    bm = BM25(DOCS)
    assert bm.scores(["sofa"])[2] > bm.scores(["nha"])[0]


def test_corpus_rong_khong_loi():
    assert BM25([]).scores(["a"]) == []