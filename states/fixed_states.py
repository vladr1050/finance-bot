from aiogram.fsm.state import State, StatesGroup

class AddFixedExpenseState(StatesGroup):
    name = State()
    amount = State()

class EditFixedExpenseState(StatesGroup):
    select_expense = State()
    new_name = State()
    new_amount = State()

class DeleteFixedExpenseState(StatesGroup):
    select_expense = State()