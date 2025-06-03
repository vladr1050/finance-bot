# app/states/expense_states.py

from aiogram.fsm.state import StatesGroup, State

class AddExpenseStates(StatesGroup):
    choosing_category = State()
    entering_amount = State()

class EditExpenseStates(StatesGroup):
    choosing_expense = State()
    entering_new_amount = State()
    choosing_new_category = State()
    entering_new_comment = State()

class DeleteExpenseStates(StatesGroup):
    choosing_expense = State()
    confirming_deletion = State()
