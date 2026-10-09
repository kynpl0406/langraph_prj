import os
import uuid
from datetime import datetime

import pytest
from pymongo import MongoClient

# Ghi đè THẲNG (không dùng setdefault) để dù .env có URI Atlas và key Gemini thật,
# test cũng không bao giờ dùng tới. Phải đặt trước khi import app.
os.environ["MONGO_URI"] = "mongodb://localhost:27018"
os.environ["MONGO_DB"] = "home_services_unused"
os.environ["GOOGLE_API_KEY"] = "fake-key"

TEST_MONGO_URI = os.getenv("TEST_MONGO_URI", "mongodb://localhost:27018")


@pytest.fixture
def test_db(monkeypatch):
    """Mongo THẬT, nhưng là database riêng: tạo mới mỗi test, xóa sau khi xong."""
    client = MongoClient(TEST_MONGO_URI, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    except Exception as e:
        pytest.fail(
            f"Không kết nối được Mongo test tại {TEST_MONGO_URI}. "
            f"Đã chạy 'docker start mongo-test' chưa? Lỗi: {type(e).__name__}"
        )

    name = f"home_services_test_{uuid.uuid4().hex[:8]}"
    db = client[name]

    db.categories.insert_many(
        [
            {
                "code": "dien_nuoc",
                "name": {"vi": "Điện nước", "en": "Electrical & plumbing"},
                "aliases": ["thợ điện nước", "sửa điện nước"],
            },
            {
                "code": "ve_sinh",
                "name": {"vi": "Vệ sinh", "en": "Cleaning"},
                "aliases": ["dọn nhà", "vệ sinh nhà"],
            },
            {
                "code": "house_cleaning",
                "name": {"vi": "Dọn dẹp nhà cửa", "en": "House cleaning"},
                "aliases": ["giúp việc"],
            },
        ]
    )

    db.providers.insert_many(
        [
            {
                "provider_name": "Vệ Sinh Nhà SG",
                "description": "Dọn vệ sinh nhà theo giờ tại Thủ Đức. Có chi nhánh CN5 Quận 9.",
                "category_codes": ["house_cleaning", "ve_sinh"],
                "pricing": [
                    {
                        "label": "Dọn nhà không định kỳ",
                        "pricing_type": "fixed",
                        "price_min": 95000,
                        "price_unit": "per_hour",
                        "currency": "VND",
                    },
                    {
                        "label": "Dọn nhà định kỳ",
                        "pricing_type": "range",
                        "price_min": 70000,
                        "price_max": 85000,
                        "price_unit": "per_hour",
                        "currency": "VND",
                    },
                    {"label": "Giúp việc theo tháng", "pricing_type": "quote_based"},
                ],
                "phones": [
                    {"raw": "0767 448 555", "e164": "+84767448555", "is_primary": True},
                    {"raw": "0767 224 555", "e164": "+84767224555", "is_primary": False},
                    {"raw": "0926 810 111", "e164": "+84926810111", "is_primary": False},
                ],
                "service_coverage": {"type": "areas", "raw_text": "Thủ Đức và các quận lân cận"},
                "location": {
                    "address_line": "77/8 Đường Số 16, KP3",
                    "district": {"name": "TP Thủ Đức"},
                    "ward": {"name": "Phường Hiệp Bình Chánh"},
                    "province": {"name": "Thành phố Hồ Chí Minh"},
                },
                "provider_status": "pending_review",
                "review": {"status": "pending"},
                "evidences": [{"field": "pricing", "quote": "..."}],
                "created_at": datetime(2026, 10, 3),
            },
            {
                "provider_name": "Thợ Điện Nước 24h",
                "description": "Sửa điện nước tại nhà, có mặt trong 30 phút.",
                "category_codes": ["dien_nuoc"],
                "pricing": [
                    {
                        "label": "Công thợ",
                        "pricing_type": "fixed",
                        "price_min": 150000,
                        "price_unit": "per_visit",
                        "currency": "VND",
                    }
                ],
                "phones": [{"raw": "0900 111 222", "e164": "+84900111222", "is_primary": True}],
                "service_coverage": {"type": "areas", "raw_text": "Quận 7, Quận 4"},
                "location": {
                    "address_line": "12 Nguyễn Thị Thập",
                    "district": {"name": "Quận 7"},
                    "province": {"name": "Thành phố Hồ Chí Minh"},
                },
                "provider_status": "pending_review",
            },
            {
                "provider_name": "Dọn Dẹp Xanh",
                "description": "Vệ sinh văn phòng và nhà ở.",
                "category_codes": ["ve_sinh"],
                "pricing": [
                    {
                        "label": "Theo giờ",
                        "pricing_type": "fixed",
                        "price_min": 120000,
                        "price_unit": "per_hour",
                        "currency": "VND",
                    }
                ],
                "phones": [],
                "service_coverage": {"type": "areas", "raw_text": "Quận 1, Quận 3"},
                "location": {
                    "address_line": "5 Lê Lợi",
                    "district": {"name": "Quận 1"},
                    "province": {"name": "Thành phố Hồ Chí Minh"},
                },
                "provider_status": "pending_review",
            },
        ]
    )

    # tools.py và nodes.py dùng "from app.db import db" nên phải thay ở từng module
    monkeypatch.setattr("app.tools.db", db)
    monkeypatch.setattr("app.nodes.db", db)

    yield db

    client.drop_database(name)
    client.close()
