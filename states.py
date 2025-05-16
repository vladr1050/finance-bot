from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    waiting_for_name = State()
    waiting_for_income = State()

class AddFixedExpense(StatesGroup):
    waiting_for_name = State()
    waiting_for_amount = State()
    waiting_for_more = State()

class EditIncome(StatesGroup):
    waiting_for_new_income = State()

class EditExpense(StatesGroup):
    waiting_for_new_value = State()
    waiting_for_field_choice = State()

class AddDailyExpense(StatesGroup):
    choosing_category = State()
    entering_amount = State()
    entering_comment = State()

class AddCategory(StatesGroup):
    entering_name = State()

class EditDailyExpense(StatesGroup):
    choosing_field = State()
    editing_amount = State()
    editing_comment = State()
