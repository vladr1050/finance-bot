import asyncio
from aiogram import Bot, Dispatcher
from startup import setup_bot

print("⚙️ Starting bot...")

async def main():
    await setup_bot()

if __name__ == "__main__":
    asyncio.run(main())
