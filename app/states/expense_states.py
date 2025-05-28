# app/states/expense_states.py

from aiogram.fsm.state import StatesGroup, State

class AddExpenseStates(StatesGroup):
    choosing_category = State()
    entering_amount = State()
