from bot_setup import dp
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import delete
from db.database import async_session
from db.models import User, DailyExpense, FixedExpense, ExpenseCategory

# ✅ Команда: сброс категорий к дефолтным
@dp.message(Command("reset_categories"))
async def reset_categories(message: Message):
    if not message.from_user:
        return

    default_categories = [ ... ]

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()

        if not user:
            await message.answer("❌ User not found.")
            return

        await session.execute(
            delete(ExpenseCategory).where(ExpenseCategory.user_id == user.id)
        )
        for name in default_categories:
            session.add(ExpenseCategory(user_id=user.id, name=name))
        await session.commit()

    await message.answer("✅ Categories have been reset to default.")


# ✅ Команда: полное удаление всех данных пользователя
@dp.message(Command("wipe_data"))
async def wipe_user_data(message: Message):
    if not message.from_user:
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()

        if not user:
            await message.answer("❌ User not found.")
            return

        user_id = user.id

        await session.execute(delete(DailyExpense).where(DailyExpense.user_id == user_id))
        await session.execute(delete(FixedExpense).where(FixedExpense.user_id == user_id))
        await session.execute(delete(ExpenseCategory).where(ExpenseCategory.user_id == user_id))
        await session.delete(user)

        await session.commit()

    await message.answer("🧨 All your data has been wiped. Use /start to begin again.")

