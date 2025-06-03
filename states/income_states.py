from aiogram.fsm.state import State, StatesGroup

class IncomeState(StatesGroup):
    waiting_for_amount = State()

class IncomeEditState(StatesGroup):
    choosing_income = State()

class IncomeEditState(StatesGroup):
    waiting_for_new_amount = State()

class IncomeSetState(StatesGroup):
    waiting_for_income = State()