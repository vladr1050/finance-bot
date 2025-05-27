import asyncio
from aiogram import Bot, Dispatcher
from app.startup import setup_bot

async def main():
    await setup_bot()

if __name__ == "__main__":
    asyncio.run(main())
