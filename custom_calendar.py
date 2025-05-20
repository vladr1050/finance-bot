from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date


# Показываем первый календарь — выбор начальной даты
async def show_start_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📅 Select start date:")
    await callback.message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())
    await state.update_data(calendar_stage="start")


# Показываем второй календарь — выбор конечной даты
async def show_end_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📅 Select end date:")
    await callback.message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())
    await state.update_data(calendar_stage="end")


# Обработка выбранной даты
async def process_calendar(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected_date = callback_data.date
    data = await state.get_data()
    stage = data.get("calendar_stage")

    if stage == "start":
        await state.update_data(start_date=selected_date)
        await show_end_calendar(callback, state)

    elif stage == "end":
        await state.update_data(end_date=selected_date)
        await callback.message.edit_text(f"Selected period:\n📅 {data['start_date']} to {selected_date}")
        # ➕ Здесь можно вызвать показ расходов за диапазон
        # например: await show_expense_history_for_range(callback, data['start_date'], selected_date)
