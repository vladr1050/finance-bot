# app/repositories/forecast_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.db.models import ForecastScenario


async def create_forecast_scenario(
    session: AsyncSession,
    user_uuid: UUID,
    name: str,
    months: int,
    income_changes: float,
    fixed_changes: float,
    extra_expenses: list,
    projected_savings: float,
    daily_budget: float,
    total_free: float
):
    """
    Create a new forecast scenario for a given user.
    """
    scenario = ForecastScenario(
        user_id=user_uuid,
        name=name,
        months=months,
        income_changes=income_changes,
        fixed_changes=fixed_changes,
        extra_expenses=extra_expenses,
        projected_savings=projected_savings,
        daily_budget=daily_budget,
        total_free=total_free
    )
    session.add(scenario)
    await session.commit()
    return scenario


async def list_user_forecasts(session: AsyncSession, user_uuid: UUID):
    """
    Return all forecast scenarios for the given user.
    """
    result = await session.execute(
        select(ForecastScenario).where(ForecastScenario.user_id == user_uuid)
    )
    return result.scalars().all()


async def get_forecast_by_id(session: AsyncSession, user_uuid: UUID, forecast_id: int):
    """
    Retrieve a specific forecast scenario by its ID and user.
    """
    result = await session.execute(
        select(ForecastScenario).where(
            ForecastScenario.user_id == user_uuid,
            ForecastScenario.id == forecast_id
        )
    )
    return result.scalar_one_or_none()


async def delete_forecast_by_id(session: AsyncSession, user_uuid: UUID, forecast_id: int):
    """
    Delete a specific forecast scenario by ID.
    """
    forecast = await get_forecast_by_id(session, user_uuid, forecast_id)
    if forecast:
        await session.delete(forecast)
        await session.commit()
        return True
    return False
