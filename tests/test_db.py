import json
from datetime import datetime

from bson import ObjectId

from app.db import to_plain


def test_to_plain_doi_objectid_va_datetime_sang_chuoi():
    oid = ObjectId()
    data = to_plain({"_id": oid, "created_at": datetime(2026, 10, 3), "ten": "Điện"})

    assert data["_id"] == str(oid)
    assert isinstance(data["created_at"], str)
    assert data["ten"] == "Điện"
    json.dumps(data)  # phải serialize được, không ném lỗi
