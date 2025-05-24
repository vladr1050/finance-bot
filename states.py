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

class BudgetAdjustmentFSM(StatesGroup):
    choosing_operation = State()       # Add / Subtract
    entering_amount = State()
    entering_comment = State()
    choosing_permanency = State()
    confirm_recalculation = State()

class ForecastScenarioFSM(StatesGroup):
    choosing_months = State()
    entering_income_change = State()
    entering_fixed_change = State()
    entering_savings_goal = State()
    entering_extra_expenses = State()
    confirming = State()

