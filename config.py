import os

if os.getenv("RAILWAY_ENVIRONMENT_ID") is None:
    from dotenv import load_dotenv
    load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_URL = os.getenv("DB_URL")
