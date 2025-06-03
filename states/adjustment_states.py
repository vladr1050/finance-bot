from aiogram.fsm.state import StatesGroup, State

class BudgetAdjustmentFSM(StatesGroup):
    choosing_category = State()
    choosing_type = State()
    entering_amount = State()
    entering_comment = State()
    choosing_permanence = State()
    confirm = State()
