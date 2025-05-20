from aiogram.types import CallbackQuery
from aiogram_calendar import SimpleCalendar
from aiogram.fsm.context import FSMContext
from datetime import date
from keyboards import main_menu

async def show_start_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📅 Select the **start date**:")
    await callback.message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())
    await state.update_data(calendar_stage="start")


async def show_end_calendar(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📅 Select the **end date**:")
    await callback.message.edit_reply_markup(reply_markup=await SimpleCalendar().start_calendar())
    await state.update_data(calendar_stage="end")


async def process_calendar(callback: CallbackQuery, callback_data: dict, state: FSMContext, handler_fn):
    selected, selected_date = await SimpleCalendar().process_selection(callback, callback_data)

    if selected:
        data = await state.get_data()
        stage = data.get("calendar_stage")
        print(f"📍 Calendar stage: {stage}")
        print(f"📍 Selected date: {selected_date}")

        if stage == "start":
            await state.update_data(start_date=selected_date)
            await show_end_calendar(callback, state)

        elif stage == "end":
            start_date = data.get("start_date")
            end_date = selected_date

            if not start_date or start_date > end_date:
                await callback.message.answer("❌ Invalid date range. Start must be before End.", reply_markup=main_menu())
                await state.clear()
                return

            await state.clear()
            await handler_fn(callback, start_date, end_date)


