from aiogram import Router, F
from aiogram.types import Message

start_router = Router()

@start_router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("✅ Bot is running and start command works!")
