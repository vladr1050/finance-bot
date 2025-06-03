# init_db.py

import asyncio
from app.db.database import init_db

if __name__ == "__main__":
    asyncio.run(init_db())
