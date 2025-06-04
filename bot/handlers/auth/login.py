from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.auth_service import authenticate_user

router = Router()

class LoginFSM(StatesGroup):
    email = State()
    password = State()

@router.callback_query(F.data == "start_login")
async def start_login(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📧 Enter your email:")
    await state.set_state(LoginFSM.email)
    await callback.answer()

@router.message(LoginFSM.email)
async def login_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await message.answer("🔑 Enter your password:")
    await state.set_state(LoginFSM.password)

@router.message(LoginFSM.password)
async def login_password(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await authenticate_user(data["email"], message.text.strip())

    if user:
        await state.clear()
        await state.update_data(user_uuid=str(user.user_uuid))  # ✅ Сохраняем UUID

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Income", callback_data="menu_income")],
            [InlineKeyboardButton(text="🏠 Fixed Expenses", callback_data="menu_fixed")],
            [InlineKeyboardButton(text="📅 Daily Expenses", callback_data="menu_expenses")],
            [InlineKeyboardButton(text="💾 Savings", callback_data="menu_savings")],
            [InlineKeyboardButton(text="📊 Forecast", callback_data="menu_forecast")],
            [InlineKeyboardButton(text="🛠 Adjust Budget", callback_data="menu_adjust")],
            [InlineKeyboardButton(text="📒 History", callback_data="menu_history")]
        ])
        await message.answer("✅ Logged in successfully!\n\nChoose what you'd like to do:", reply_markup=keyboard)
    else:
        await state.clear()
        await message.answer("❌ Invalid email or password. Try again.")
