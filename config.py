import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Логируем, чтобы убедиться, что всё загружено
print(f"👉 ENV BOT_TOKEN: {os.getenv('BOT_TOKEN')}")
print(f"👉 ENV DB_URL: {os.getenv('DB_URL')}")

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_URL = os.getenv("DB_URL")

    @staticmethod
    def is_valid():
        return all([Config.BOT_TOKEN, Config.DB_URL])
