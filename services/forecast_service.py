# app/services/forecast_service.py

from uuid import UUID
from db.database import async_session
from repositories.forecast_repository import (
    create_forecast_scenario,
    list_user_forecasts,
    get_forecast_by_id,
    delete_forecast_by_id
)


async def save_forecast(
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
    Save a new forecast scenario for the given user.
    """
    async with async_session() as session:
        return await create_forecast_scenario(
            session=session,
            user_uuid=user_uuid,
            name=name,
            months=months,
            income_changes=income_changes,
            fixed_changes=fixed_changes,
            extra_expenses=extra_expenses,
            projected_savings=projected_savings,
            daily_budget=daily_budget,
            total_free=total_free
        )


async def get_user_forecasts(user_uuid: UUID):
    """
    Retrieve all forecast scenarios for a user.
    """
    async with async_session() as session:
        return await list_user_forecasts(session, user_uuid)


async def get_forecast(user_uuid: UUID, forecast_id: int):
    """
    Retrieve a specific forecast scenario by ID.
    """
    async with async_session() as session:
        return await get_forecast_by_id(session, user_uuid, forecast_id)


async def delete_forecast(user_uuid: UUID, forecast_id: int):
    """
    Delete a forecast scenario by ID.
    """
    async with async_session() as session:
        return await delete_forecast_by_id(session, user_uuid, forecast_id)
