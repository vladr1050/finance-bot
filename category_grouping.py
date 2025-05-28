# category_grouping.py

from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from app.db.models import User, ExpenseCategory
from app.db.database import async_session
from states import AddDailyExpense
from sqlalchemy import select

CATEGORY_GROUPS = {
    "🏠 Housing": ["Rent / Mortgage", "Utilities", "Home maintenance"],
    "🍽 Food & Drinks": ["Groceries", "Restaurants", "Coffee / Snacks"],
    "🚗 Transport": ["Fuel", "Public Transport", "Car Maintenance", "Parking / Taxi"],
    "🛍 Shopping": ["Clothing", "Household Goods", "Electronics"],
    "🧘‍♂️ Health & Fitness": ["Medical", "Pharmacy", "Gym / Fitness"],
    "🎉 Entertainment": ["Cinema / Theater", "Subscriptions / Streaming", "Travel"],
    "👨‍👩‍👧‍👦 Family & Kids": ["Education", "Kids supplies", "Gifts & Holidays"],
    "💼 Finance & Obligations": ["Loans / Debts", "Insurance", "Taxes"],
    "🐾 Other": ["Charity", "Pets", "Miscellaneous"]
}

def get_group_selection_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=group, callback_data=f"group_{i}")]
        for i, group in enumerate(CATEGORY_GROUPS.keys())
    ] + [[InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]])
    return keyboard

def get_category_keyboard(categories, group_index):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")]
        for cat in categories
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data=f"back_to_groups_{group_index}")]])
    return keyboard

# ——— Handlers (подключаются в main.py) ———

def register_category_group_handlers(dp):
    @dp.callback_query(F.data == "daily_expense")
    async def open_category_group_menu(callback: CallbackQuery, state: FSMContext):
        await state.set_state(AddDailyExpense.choosing_category)
        await callback.message.answer("Select a category group:", reply_markup=get_group_selection_keyboard())
        await callback.answer()

    @dp.callback_query(F.data.startswith("group_"))
    async def show_categories_in_group(callback: CallbackQuery, state: FSMContext):
        group_index = int(callback.data.split("_")[1])
        group_name = list(CATEGORY_GROUPS.keys())[group_index]
        category_names = CATEGORY_GROUPS[group_name]

        async with async_session() as session:
            user_result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
            user = user_result.scalar()

            if not user:
                await callback.message.answer("❌ User not found. Please use /start.")
                await callback.answer()
                return

            result = await session.execute(
                select(ExpenseCategory).where(
                    ExpenseCategory.user_id == user.id,
                    ExpenseCategory.name.in_(category_names)
                )
            )
            user_cats = result.scalars().all()

        if not user_cats:
            await callback.message.answer("⚠️ No categories found in this group.")
            await callback.answer()
            return

        await callback.message.edit_text(
            f"{group_name} categories:",
            reply_markup=get_category_keyboard(user_cats, group_index)
        )
        await callback.answer()

    @dp.callback_query(F.data.startswith("back_to_groups_"))
    async def go_back_to_groups(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_text("Select a category group:", reply_markup=get_group_selection_keyboard())
        await callback.answer()
