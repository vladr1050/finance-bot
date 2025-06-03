from aiogram.fsm.state import StatesGroup, State

class HistoryFSM(StatesGroup):
    selecting_date = State()
    viewing_day = State()

class EditExpenseFSM(StatesGroup):
    editing_category = State()
    editing_amount = State()

class RangeHistoryFSM(StatesGroup):
    selecting_start = State()
    selecting_end = State()

class CategoryReportFSM(StatesGroup):
    selecting_start = State()
    selecting_end = State()
