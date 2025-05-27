from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.states.income_states import IncomeState
from app.services.income_service import add_income_for_user

income_router = Router()

@income_router.message(F.text.lower() == "/add_income")
async def start_add_income(message: Message, state: FSMContext):
    await message.answer("💰 Enter income amount:")
    await state.set_state(IncomeState.waiting_for_amount)


@income_router.message(IncomeState.waiting_for_amount)
async def process_income_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Please enter a valid number.")
        return

    # Сохраняем в БД через сервис
    await add_income_for_user(user_id=message.from_user.id, amount=amount)

    await message.answer(f"✅ Income of {amount:.2f} saved.")
    await state.clear()
