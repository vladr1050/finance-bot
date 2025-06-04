# app/bot/handlers/adjustments/add.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import date

from repositories.monthly_budget_adjustment import add_adjustment
from db.database import async_session
from states.adjustment_states import BudgetAdjustmentFSM

router = Router()

@router.message(Command("adjust_budget"))
async def start_adjustment(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Income", callback_data="adj_cat_income")],
        [InlineKeyboardButton(text="🏠 Fixed Expense", callback_data="adj_cat_fixed")],
        [InlineKeyboardButton(text="💾 Savings", callback_data="adj_cat_savings")]
    ])
    await message.answer("📊 What part of the budget do you want to adjust?", reply_markup=keyboard)
    await state.set_state(BudgetAdjustmentFSM.choosing_category)


@router.callback_query(BudgetAdjustmentFSM.choosing_category, F.data.startswith("adj_cat_"))
async def choose_category(callback: CallbackQuery, state: FSMContext):
    source = callback.data.replace("adj_cat_", "")
    await state.update_data(source=source)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="adj_type_add")],
        [InlineKeyboardButton(text="➖ Subtract", callback_data="adj_type_subtract")]
    ])
    await callback.message.edit_text("Do you want to *add* or *subtract*?", reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(BudgetAdjustmentFSM.choosing_type)
    await callback.answer()


@router.callback_query(BudgetAdjustmentFSM.choosing_type, F.data.startswith("adj_type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext):
    adj_type = callback.data.replace("adj_type_", "")
    await state.update_data(adj_type=adj_type)
    await callback.message.edit_text("💵 Enter the amount:")
    await state.set_state(BudgetAdjustmentFSM.entering_amount)
    await callback.answer()


@router.message(BudgetAdjustmentFSM.entering_amount, F.text.regexp(r"^\d+(\.\d{1,2})?$"))
async def enter_amount(message: Message, state: FSMContext):
    await state.update_data(amount=float(message.text.strip()))
    await message.answer("📝 Enter a comment (optional) or type '-' to skip:")
    await state.set_state(BudgetAdjustmentFSM.entering_comment)


@router.message(BudgetAdjustmentFSM.entering_comment)
async def enter_comment(message: Message, state: FSMContext):
    comment = message.text.strip()
    if comment == "-":
        comment = None
    await state.update_data(comment=comment)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌙 Only for this month", callback_data="adj_perm_no")],
        [InlineKeyboardButton(text="♾ Apply permanently", callback_data="adj_perm_yes")]
    ])
    await message.answer("Should this adjustment apply permanently or only for this month?", reply_markup=keyboard)
    await state.set_state(BudgetAdjustmentFSM.choosing_permanence)


@router.callback_query(BudgetAdjustmentFSM.choosing_permanence, F.data.startswith("adj_perm_"))
async def confirm_adjustment(callback: CallbackQuery, state: FSMContext):
    apply_permanently = callback.data == "adj_perm_yes"
    await state.update_data(apply_permanently=apply_permanently)

    data = await state.get_data()
    user_uuid = data.get("user_uuid")

    if not user_uuid:
        await callback.message.edit_text("❌ You are not logged in. Please /login first.")
        await callback.answer()
        return

    month_start = date.today().replace(day=1)

    async with async_session() as session:
        await add_adjustment(
            session=session,
            user_id=user_uuid,
            month=month_start,
            source=data["source"],
            adjustment_type=data["adj_type"],
            amount=data["amount"],
            comment=data["comment"],
            apply_permanently=data["apply_permanently"]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add another", callback_data="add_adjust_again")],
        [InlineKeyboardButton(text="📋 View adjustments", callback_data="view_adjustments")],
        [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
    ])
    await callback.message.edit_text("✅ Adjustment saved successfully.", reply_markup=keyboard)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "add_adjust_again")
async def repeat_adjust_flow(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Income", callback_data="adj_cat_income")],
        [InlineKeyboardButton(text="🏠 Fixed Expense", callback_data="adj_cat_fixed")],
        [InlineKeyboardButton(text="💾 Savings", callback_data="adj_cat_savings")]
    ])
    await callback.message.edit_text("📊 What part of the budget do you want to adjust?", reply_markup=keyboard)
    await state.set_state(BudgetAdjustmentFSM.choosing_category)
    await callback.answer()
