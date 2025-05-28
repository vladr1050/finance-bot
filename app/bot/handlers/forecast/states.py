from aiogram.fsm.state import StatesGroup, State

class ForecastScenarioFSM(StatesGroup):
    choosing_months = State()
    entering_income_change = State()
    entering_fixed_change = State()
    entering_savings_goal = State()
    entering_extra_expenses = State()
    confirming = State()
