# app/bot/handlers/auth/registration.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.services.auth_service import register_user

router = Router()

class RegistrationFSM(StatesGroup):
    email = State()
    password = State()
    confirm = State()

@router.callback_query(F.data == "start_register")
async def start_register(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📧 Please enter your email:")
    await state.set_state(RegistrationFSM.email)
    await callback.answer()

@router.message(RegistrationFSM.email)
async def reg_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await message.answer("🔑 Create a password:")
    await state.set_state(RegistrationFSM.password)

@router.message(RegistrationFSM.password)
async def reg_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await message.answer("🔁 Confirm your password:")
    await state.set_state(RegistrationFSM.confirm)

@router.message(RegistrationFSM.confirm)
async def reg_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.strip() != data["password"]:
        await message.answer("❌ Passwords do not match. Please try again.")
        return await state.clear()
    try:
        await register_user(
            email=data["email"],
            password=data["password"],
            telegram_id=message.from_user.id
        )
        await message.answer("✅ Registration complete. Use /start to begin.")
    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    await state.clear()
