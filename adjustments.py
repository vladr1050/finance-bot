from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, delete
from datetime import date, datetime, timedelta

from db.models import MonthlyBudgetAdjustment, User, FixedExpense, MonthlyBudget, DailyExpense
from db.database import async_session
from states import BudgetAdjustmentFSM
from keyboards import main_menu
from bot_setup import dp

# === Save adjustment ===
async def save_adjustment(user_id, source, type_, amount, comment, permanent):
    month = date.today().replace(day=1)
    async with async_session() as session:
        adjustment = MonthlyBudgetAdjustment(
            user_id=user_id,
            month=month,
            source=source,
            type=type_,
            amount=amount,
            comment=comment,
            apply_permanently=1 if permanent else 0,
            processed=1,
            created_at=datetime.utcnow()
        )
        session.add(adjustment)
        await session.commit()


# === FSM START (Edit Income / Savings) ===
@dp.callback_query(F.data == "edit_income")
async def edit_income_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(source="income")
    await state.set_state(BudgetAdjustmentFSM.choosing_operation)
    await callback.message.answer("Choose type of change:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="adjust_add")],
        [InlineKeyboardButton(text="➖ Subtract", callback_data="adjust_subtract")]
    ]))
    await callback.answer()


@dp.callback_query(F.data == "set_savings")
async def edit_savings_goal_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(source="savings")
    await state.set_state(BudgetAdjustmentFSM.choosing_operation)
    await callback.message.answer("Adjust your monthly savings goal:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="adjust_add")],
        [InlineKeyboardButton(text="➖ Subtract", callback_data="adjust_subtract")]
    ]))
    await callback.answer()


# === Edit Fixed Expenses per item ===
@dp.callback_query(F.data == "edit_expense")
async def show_fixed_expense_list(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(
            select(FixedExpense).join(User).where(User.telegram_id == callback.from_user.id)
        )
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.answer("❌ You have no fixed expenses.")
        await callback.answer()
        return

    keyboard = []
    for exp in expenses:
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {exp.name}: €{exp.amount:.2f}",
                callback_data=f"edit_fixed_{exp.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")])
    await callback.message.answer("Select an expense to adjust:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_fixed_"))
async def start_edit_fixed(callback: CallbackQuery, state: FSMContext):
    expense_id = int(callback.data.split("_")[-1])
    await state.update_data(fixed_expense_id=expense_id, source="fixed_expense")
    await state.set_state(BudgetAdjustmentFSM.choosing_operation)
    await callback.message.answer("Choose type of change:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add", callback_data="adjust_add")],
        [InlineKeyboardButton(text="➖ Subtract", callback_data="adjust_subtract")]
    ]))
    await callback.answer()


@dp.callback_query(F.data.in_(["adjust_add", "adjust_subtract"]))
async def adjustment_choose_amount(callback: CallbackQuery, state: FSMContext):
    await state.update_data(adjust_type="add" if callback.data == "adjust_add" else "subtract")
    await state.set_state(BudgetAdjustmentFSM.entering_amount)
    await callback.message.answer("Enter amount (€):")
    await callback.answer()


@dp.message(BudgetAdjustmentFSM.entering_amount)
async def adjustment_enter_comment(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Please enter a valid positive number.")
        return
    await state.update_data(amount=amount)
    await state.set_state(BudgetAdjustmentFSM.entering_comment)
    await message.answer("Add comment (optional):")


@dp.message(BudgetAdjustmentFSM.entering_comment)
async def adjustment_choose_permanency(message: Message, state: FSMContext):
    await state.update_data(comment=message.text.strip())
    await state.set_state(BudgetAdjustmentFSM.choosing_permanency)
    await message.answer("Should this adjustment be permanent?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes", callback_data="perm_yes")],
        [InlineKeyboardButton(text="❌ No, only this month", callback_data="perm_no")]
    ]))


@dp.callback_query(F.data.in_(["perm_yes", "perm_no"]))
async def finalize_adjustment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await save_adjustment(
        user_id=callback.from_user.id,
        source=data["source"],
        type_=data["adjust_type"],
        amount=data["amount"],
        comment=data["comment"],
        permanent=(callback.data == "perm_yes")
    )
    await callback.message.answer("✅ Adjustment saved.", reply_markup=main_menu())
    await state.clear()
    await callback.answer()


# === View Adjustments History ===
@dp.message(Command("adjustments"))
async def show_adjustments(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar()

        if not user:
            await message.answer("❌ User not found. Use /start")
            return

        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user.id
            ).order_by(MonthlyBudgetAdjustment.created_at.desc()).limit(20)
        )
        adjustments = result.scalars().all()

        if not adjustments:
            await message.answer("📭 No adjustments found.")
            return

        for adj in adjustments:
            text = (
                f"🗓 {adj.month.strftime('%Y-%m')}\n"
                f"📌 Source: {adj.source}\n"
                f"{('➕' if adj.type == 'add' else '➖')} Amount: €{adj.amount:.2f}\n"
                f"📝 {adj.comment or '-'}\n"
                f"🔁 Permanent: {'✅' if adj.apply_permanently else '❌'}\n"
                f"📦 Processed: {'✅' if adj.processed else '❌'}"
            )
            buttons = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_adj_{adj.id}")]
                ]
            )
            await message.answer(text, reply_markup=buttons)


@dp.callback_query(F.data.startswith("delete_adj_"))
async def delete_adj_callback(callback: CallbackQuery):
    adj_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()

        if not user:
            await callback.message.answer("❌ User not found.")
            await callback.answer()
            return

        await session.execute(
            delete(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.id == adj_id,
                MonthlyBudgetAdjustment.user_id == user.id
            )
        )
        await session.commit()
        await callback.message.edit_text("🗑 Adjustment deleted.")
        await callback.answer()


# === Register if needed ===
def register_adjustment_handlers(dp):
    pass
