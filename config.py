import os
import logging
from dotenv import load_dotenv

# Load .env variables for local dev
load_dotenv()

# Detect environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
IS_DEV = ENVIRONMENT == "development"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logging.info(f"🔧 ENVIRONMENT: {ENVIRONMENT}")
logging.info(f"🔐 BOT_TOKEN: {os.getenv('BOT_TOKEN')[:10]}...")
logging.info(f"🛢 DATABASE_URL: {os.getenv('DATABASE_URL') or os.getenv('DB_URL')}")

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")

    @staticmethod
    def is_valid():
        return all([Config.BOT_TOKEN, Config.DB_URL])
