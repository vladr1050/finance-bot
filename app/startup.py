import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app.bot.handlers.register_all_handlers import register_all_handlers
from app.config import Config

config = Config()
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

async def setup_bot():
    logging.basicConfig(level=logging.INFO)
    register_all_handlers(dp)
    await dp.start_polling(bot)
