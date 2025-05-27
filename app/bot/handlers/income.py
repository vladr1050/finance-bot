from aiogram import Router, F
from aiogram.types import Message

income_router = Router()

@income_router.message(F.text.lower().startswith("income"))
async def handle_income(message: Message):
    await message.answer("🪙 Income handler is active!")
