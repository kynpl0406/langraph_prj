import re
import unicodedata

_WORD = re.compile(r'\w+')


def strip_accents(s):
    s = unicodedata.normalize('NFD', s.replace("đ", "d").replace("Đ", "D"))
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')


def normalize(s):
    return strip_accents(s or "").lower()


def tokenize(s):
    """Tu don + bigram. 'Ve sinh nha' -> ['ve', 'sinh', 'nha', 've_sinh', 'sinh_nha']"""
    words = _WORD.findall(normalize(s))
    bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
    return words + bigrams


def load_category_names(db):
    """code -> 'ten vi + ten en + cac tu dong nghia' de dua vao text cua provider."""
    out = {}
    for c in db.categories.find({}, {"code": 1, "name": 1, "aliases": 1}):
        name = c.get("name") or {}
        out[c["code"]] = " ".join(
            [name.get("vi", ""), name.get("en", ""), *(c.get("aliases") or [])]
        )
    return out

def provider_to_text(p, cat_names):
    """Gom cac field  qua trong cua provider thanh 1 doan text de index"""
    cat_names = cat_names or {}
    loc = p.get("location") or {}
    parts = [
        p.get("provider_name", ""),
        p.get("provider_name", ""), #lap de tang trong so
        p.get("description", ""),
        " ".join(cat_names.get(c, c) for c in p.get("category_codes") or []),
        (p.get("service_coverage") or {}).get("raw_text", ""),
        loc.get("address_line", ""),
        (loc.get("ward") or {}).get("name", ""),
        (loc.get("district") or {}).get("name", ""),
        " ".join(x.get("label", "") for x in p.get("pricing") or []),
    ]
    return "\n".join(s for s in parts if s)
        
