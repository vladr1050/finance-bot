from aiogram.fsm.state import State, StatesGroup

class SetSavingsState(StatesGroup):
    amount = State()

class AddSavingsState(StatesGroup):
    amount = State()
