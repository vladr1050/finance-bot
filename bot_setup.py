from aiogram.fsm.storage.memory import MemoryStorage
from app.config import Config
from aiogram import Bot, Dispatcher

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
