# utils/errors.py

from aiogram.types import Message
import logging

async def safe_send(message: Message, text: str):
    try:
        await message.answer(text)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")
