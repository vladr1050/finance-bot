from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.keyboards import main_menu
from aiogram.fsm.context import FSMContext
from bot.handlers.income.edit import start_edit_income
from bot.handlers.income.view import view_income
from db.database import async_session

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Register", callback_data="start_register")],
        [InlineKeyboardButton(text="🔐 Login", callback_data="start_login")]
    ])
    await message.answer(
        "👋 Welcome to your personal finance bot!\n\nPlease choose:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "menu_history")
async def menu_history(callback: CallbackQuery):
    await callback.message.answer("/history — select a day\n/history_range — view range")
    await callback.answer()

@router.callback_query(F.data == "menu_category_report")
async def menu_cat_report(callback: CallbackQuery):
    await callback.message.answer("/category_report — group by category")
    await callback.answer()

@router.callback_query(F.data == "menu_adjust")
async def menu_adjust(callback: CallbackQuery):
    await callback.message.answer("/adjust_budget — add correction\n/view_adjustments — see\n/delete_adjustments — remove")
    await callback.answer()

@router.callback_query(F.data == "menu_forecast")
async def menu_forecast(callback: CallbackQuery):
    await callback.message.answer("/forecast — simulate\n/forecasts — view\n/delete_forecast — remove")
    await callback.answer()

@router.callback_query(F.data == "menu_income")
async def menu_income(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Income", callback_data="add_income")],
        [InlineKeyboardButton(text="✏️ Edit Income", callback_data="edit_income")],
        [InlineKeyboardButton(text="📋 View Income", callback_data="view_income")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu")]
    ])
    await callback.message.edit_text("💰 *Income Menu* — What would you like to do?", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "edit_income")
async def handle_edit_income(callback: CallbackQuery, state: FSMContext):
    await start_edit_income(callback.message, state)
    await callback.answer()

@router.callback_query(F.data == "view_income")
async def handle_view_income(callback: CallbackQuery):
    await view_income(callback.message)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Income", callback_data="menu_income")],
        [InlineKeyboardButton(text="🏠 Fixed Expenses", callback_data="menu_fixed")],
        [InlineKeyboardButton(text="📅 Daily Expenses", callback_data="menu_expenses")],
        [InlineKeyboardButton(text="💾 Savings", callback_data="menu_savings")],
        [InlineKeyboardButton(text="📊 Forecast", callback_data="menu_forecast")],
        [InlineKeyboardButton(text="🛠 Adjust Budget", callback_data="menu_adjust")],
        [InlineKeyboardButton(text="📒 History", callback_data="menu_history")]
    ])
    await callback.message.edit_text("👋 Main Menu — Choose what you'd like to do:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "menu_fixed")
async def menu_fixed(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Fixed Expense", callback_data="add_fixed")],
        [InlineKeyboardButton(text="✏️ Edit Fixed Expenses", callback_data="edit_fixed")],
        [InlineKeyboardButton(text="📋 View Fixed Expenses", callback_data="view_fixed")],
        [InlineKeyboardButton(text="🗑 Delete Fixed Expense", callback_data="delete_fixed")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu")]
    ])
    await callback.message.edit_text("🏠 *Fixed Expenses Menu* — Choose an action:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "add_fixed")
async def handle_add_fixed(callback: CallbackQuery):
    await callback.message.answer("➕ Use /add_fixed to add a new fixed expense.")
    await callback.answer()

@router.callback_query(F.data == "edit_fixed")
async def handle_edit_fixed(callback: CallbackQuery):
    await callback.message.answer("✏️ Use /edit_fixed to modify your fixed expenses.")
    await callback.answer()

@router.callback_query(F.data == "view_fixed")
async def handle_view_fixed(callback: CallbackQuery):
    await callback.message.answer("📋 Use /view_fixed to see your current fixed expenses.")
    await callback.answer()

@router.callback_query(F.data == "delete_fixed")
async def handle_delete_fixed(callback: CallbackQuery):
    await callback.message.answer("🗑 Use /delete_fixed to remove a fixed expense.")
    await callback.answer()

@router.callback_query(F.data == "menu_expenses")
async def menu_expenses(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Daily Expense", callback_data="add_daily")],
        [InlineKeyboardButton(text="📋 View Today", callback_data="view_today")],
        [InlineKeyboardButton(text="📅 View by Date", callback_data="view_by_date")],
        [InlineKeyboardButton(text="📆 View Range", callback_data="view_range")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu")]
    ])
    await callback.message.edit_text("📅 *Daily Expenses Menu* — What do you want to do?", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "add_daily")
async def handle_add_daily(callback: CallbackQuery):
    await callback.message.answer("➕ Use /add_expense to record a new expense.")
    await callback.answer()

@router.callback_query(F.data == "view_today")
async def handle_view_today(callback: CallbackQuery):
    await callback.message.answer("📋 Use /today to see expenses for today.")
    await callback.answer()

@router.callback_query(F.data == "view_by_date")
async def handle_view_by_date(callback: CallbackQuery):
    await callback.message.answer("📆 Use /history to select a day from the calendar.")
    await callback.answer()

@router.callback_query(F.data == "view_range")
async def handle_view_range(callback: CallbackQuery):
    await callback.message.answer("📊 Use /history_range to view expenses over a custom period.")
    await callback.answer()

@router.callback_query(F.data == "menu_savings")
async def menu_savings(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Set Savings Goal", callback_data="set_savings")],
        [InlineKeyboardButton(text="➕ Add to Savings", callback_data="add_savings")],
        [InlineKeyboardButton(text="📋 View Savings", callback_data="view_savings")],
        [InlineKeyboardButton(text="✏️ Edit Savings", callback_data="edit_savings")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu")]
    ])
    await callback.message.edit_text("💾 *Savings Menu* — Choose an action:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "set_savings")
async def handle_set_savings(callback: CallbackQuery):
    await callback.message.answer("💰 Use /set_savings to define your monthly savings goal.")
    await callback.answer()

@router.callback_query(F.data == "add_savings")
async def handle_add_savings(callback: CallbackQuery):
    await callback.message.answer("➕ Use /add_savings to add money to your savings.")
    await callback.answer()

@router.callback_query(F.data == "view_savings")
async def handle_view_savings(callback: CallbackQuery):
    await callback.message.answer("📋 Use /view_savings to check your savings balance.")
    await callback.answer()

@router.callback_query(F.data == "edit_savings")
async def handle_edit_savings(callback: CallbackQuery):
    await callback.message.answer("✏️ Use /edit_savings to update your savings balance.")
    await callback.answer()

@router.callback_query(F.data == "menu_adjustments")
async def menu_adjustments(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Adjustment", callback_data="adj_add")],
        [InlineKeyboardButton(text="📋 View Adjustments", callback_data="adj_view")],
        [InlineKeyboardButton(text="🗑 Delete Adjustment", callback_data="adj_delete")],
        [InlineKeyboardButton(text="🔄 Recalculate Budget", callback_data="recalculate_budget")],
        [InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu")]
    ])
    await callback.message.edit_text("⚙️ *Adjustments Menu* — What do you want to do?", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "adj_add")
async def handle_adj_add(callback: CallbackQuery):
    await callback.message.answer("➕ Use /adjust_budget to create a new adjustment.")
    await callback.answer()

@router.callback_query(F.data == "adj_view")
async def handle_adj_view(callback: CallbackQuery):
    await callback.message.answer("📋 Use /view_adjustments to see all current adjustments.")
    await callback.answer()

@router.callback_query(F.data == "adj_delete")
async def handle_adj_delete(callback: CallbackQuery):
    await callback.message.answer("🗑 Use /delete_adjustments to remove an adjustment.")
    await callback.answer()

start_router = router