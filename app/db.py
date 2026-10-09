import json

from pymongo import MongoClient

from app.config import DB_NAME, MONGO_URI

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]


def to_plain(data):
    """Convert ObjectId, datetime,... to string for Gemini to read"""
    return json.loads(json.dumps(data, default=str))
