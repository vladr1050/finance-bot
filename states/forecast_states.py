from aiogram.fsm.state import StatesGroup, State

class SaveForecastState(StatesGroup):
    name = State()
    months = State()
    extra_expenses = State()
    income_change = State()
    fixed_change = State()

class DeleteForecastState(StatesGroup):
    confirm = State()

class ForecastScenarioFSM(StatesGroup):
    choosing_months = State()
    entering_income_change = State()
    entering_fixed_change = State()
    entering_extra_expenses = State()
    entering_savings_goal = State()