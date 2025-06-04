# init_db.py
import asyncio
import logging
from db.database import init_db

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    asyncio.run(init_db())
