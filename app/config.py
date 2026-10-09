import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ["MONGO_URI"]
DB_NAME = os.environ.get("MONGO_DB")
MODEL_NAME = "gemini-2.5-flash"
