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
import logging
logger = logging.getLogger(__name__)

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
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add", callback_data="adjust_add"),
            InlineKeyboardButton(text="➖ Subtract", callback_data="adjust_subtract")
        ],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])
    await callback.message.answer("Choose type of change:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "set_savings")
async def edit_savings_goal_start(callback: CallbackQuery, state: FSMContext):
    await state.update_data(source="savings")
    await state.set_state(BudgetAdjustmentFSM.choosing_operation)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Add", callback_data="adjust_add"),
            InlineKeyboardButton(text="➖ Subtract", callback_data="adjust_subtract")
        ],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")]
    ])
    await callback.message.answer("Adjust your monthly savings goal:", reply_markup=keyboard)
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
    amount_str = message.text.replace(",", ".").strip()

    try:
        amount = float(amount_str)
        if amount <= 0:
            await message.answer("🚫 Amount must be greater than zero. Please enter a valid number.")
            return
    except ValueError:
        logging.warning(f"[Adjustment] Invalid amount from user {message.from_user.id}: '{message.text}'")
        await message.answer("❗ Please enter a valid number (e.g., 100 or 200.50).")
        return

    await state.update_data(amount=amount)
    await state.set_state(BudgetAdjustmentFSM.entering_comment)
    await message.answer("📝 Add comment (optional):")


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


# === Recalculate Budget Flow ===
@dp.callback_query(F.data == "recalculate_budget")
async def confirm_recalc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BudgetAdjustmentFSM.confirm_recalculation)
    await callback.message.answer("Are you sure you want to recalculate the budget?\nThis cannot be undone.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes", callback_data="recalc_yes")],
        [InlineKeyboardButton(text="❌ No", callback_data="main_menu")]
    ]))
    await callback.answer()


@dp.callback_query(F.data == "recalc_yes")
async def recalc_budget_now(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()
        if not user:
            await callback.message.answer("❌ User not found.")
            await callback.answer()
            return

        today = date.today()
        month_start = today.replace(day=1)
        month_end = month_start.replace(month=month_start.month % 12 + 1, day=1) - timedelta(days=1)
        total_days = month_end.day

        income = user.monthly_income or 0
        savings_goal = user.monthly_savings or 0

        result = await session.execute(select(func.sum(FixedExpense.amount)).where(FixedExpense.user_id == user.id))
        fixed_total = result.scalar() or 0

        result = await session.execute(
            select(func.min(DailyExpense.created_at)).where(
                DailyExpense.user_id == user.id,
                func.date(DailyExpense.created_at) >= month_start
            )
        )
        first_expense_date = result.scalar()
        from_date = first_expense_date.date() if first_expense_date else today

        days_left = (month_end - from_date).days + 1
        coefficient = days_left / total_days if total_days else 1.0

        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user.id,
                MonthlyBudgetAdjustment.month == month_start,
                MonthlyBudgetAdjustment.processed == 1
            )
        )
        adjustments = result.scalars().all()
        for adj in adjustments:
            delta = adj.amount if adj.type == 'add' else -adj.amount
            if adj.source == "income":
                income += delta
            elif adj.source == "fixed_expense":
                fixed_total += delta
            elif adj.source == "savings":
                savings_goal += delta

        full_remaining = income - fixed_total - savings_goal
        remaining = full_remaining * coefficient

        result = await session.execute(
            select(MonthlyBudget).where(
                MonthlyBudget.user_id == user.id,
                MonthlyBudget.month_start == month_start
            )
        )
        budget = result.scalar()
        if budget:
            budget.income = income
            budget.fixed = fixed_total
            budget.savings_goal = savings_goal
            budget.remaining = remaining
            budget.coefficient = coefficient
            await session.commit()

        await callback.message.answer("🔄 Budget successfully recalculated.", reply_markup=main_menu())
    await callback.answer()


# === View Adjustments History ===
@dp.message(Command("adjustments"))
async def show_adjustments(message: Message, user_id: int | None = None):
    async with async_session() as session:
        if user_id is None:
            user_id = message.from_user.id

        logger.info(f"🔍 Looking up user by telegram_id={user_id}")
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar()

        if not user:
            logger.warning(f"❌ User with telegram_id={message.from_user.id} not found in DB.")
            await message.answer("❌ User not found. Use /start")
            return

        logger.info(f"✅ Found user id={user.id}, fetching adjustments...")
        result = await session.execute(
            select(MonthlyBudgetAdjustment).where(
                MonthlyBudgetAdjustment.user_id == user.id
            ).order_by(MonthlyBudgetAdjustment.created_at.desc()).limit(20)
        )
        adjustments = result.scalars().all()

        logger.info(f"📦 Retrieved {len(adjustments)} adjustments for user id={user.id}")

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

@dp.callback_query(F.data == "view_adjustments")
async def view_adjustments_menu(callback: CallbackQuery):
    await show_adjustments(callback.message, user_id=callback.from_user.id)
    await callback.answer()

@dp.message(Command("adjustments"))
async def show_adjustments_command(message: Message):
    await show_adjustments(message)

@dp.callback_query(F.data.startswith("delete_adj_"))
async def delete_adj_callback(callback: CallbackQuery):
    adj_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        logger.info(f"🗑 Delete request for adjustment_id={adj_id} from telegram_id={callback.from_user.id}")
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar()

        if not user:
            logger.warning(f"❌ User with telegram_id={callback.from_user.id} not found during deletion.")
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
        logger.info(f"✅ Adjustment {adj_id} deleted for user_id={user.id}")
        await callback.message.edit_text("🗑 Adjustment deleted.")
        await callback.answer()


# === Register if needed ===
def register_adjustment_handlers(dp):
    pass
