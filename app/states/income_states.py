from aiogram.fsm.state import State, StatesGroup

class IncomeState(StatesGroup):
    waiting_for_amount = State()
