import os

from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ["MONGO_URI"]
DB_NAME = os.getenv("MONGO_DB") or "home_services"
MODEL_NAME = "gemini-2.5-flash"