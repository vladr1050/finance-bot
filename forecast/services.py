# forecast/services.py

from forecast.models import ForecastScenario
from db.models import User
from forecast.logic import calculate_forecast
from db.database import async_session
from sqlalchemy import select
from typing import List, Dict


async def create_forecast_scenario(
    telegram_id: int,
    name: str,
    months: int,
    income_changes: float,
    fixed_changes: float,
    savings_goal: float,
    extra_expenses: List[Dict]
) -> ForecastScenario:
    """
    Create and store a forecast scenario for a premium user.
    """
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar()

        if not user or not user.is_premium:
            raise PermissionError("Only premium users can save forecast scenarios.")

        base_income = user.monthly_income
        result = await session.execute(
            select(FixedExpense).where(FixedExpense.user_id == user.id)
        )
        fixed_expenses = result.scalars().all()
        base_fixed = sum(e.amount for e in fixed_expenses)

        forecast = calculate_forecast(
            base_income=base_income,
            base_fixed_expenses=base_fixed,
            base_savings_goal=savings_goal,
            months=months,
            income_changes=income_changes,
            fixed_changes=fixed_changes,
            extra_expenses=extra_expenses
        )

        scenario = ForecastScenario(
            user_id=user.id,
            name=name,
            months=months,
            income_changes=income_changes,
            fixed_changes=fixed_changes,
            extra_expenses=extra_expenses,
            projected_savings=forecast["projected_savings"],
            daily_budget=forecast["daily_budget"],
            total_free=forecast["total_free"]
        )

        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)
        return scenario


async def get_user_forecast_scenarios(telegram_id: int) -> List[ForecastScenario]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar()
        if not user:
            return []
        return user.forecast_scenarios


async def delete_forecast_scenario(scenario_id: int, telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar()
        if not user:
            return False

        scenario = await session.get(ForecastScenario, scenario_id)
        if not scenario or scenario.user_id != user.id:
            return False

        await session.delete(scenario)
        await session.commit()
        return True
