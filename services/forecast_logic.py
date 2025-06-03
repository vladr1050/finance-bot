# app/services/forecast_logic.py

from typing import List, Dict

def calculate_forecast(
    base_income: float,
    base_fixed_expenses: float,
    base_savings_goal: float,
    months: int,
    income_changes: float = 0.0,
    fixed_changes: float = 0.0,
    extra_expenses: List[Dict] = None
) -> Dict:
    if extra_expenses is None:
        extra_expenses = []

    monthly_income = base_income + income_changes
    monthly_fixed = base_fixed_expenses + fixed_changes

    monthly_free_cash = monthly_income - monthly_fixed - base_savings_goal
    total_free_cash = monthly_free_cash * months

    total_extra_expenses = sum(
        e["amount"] for e in extra_expenses if 0 <= e["month_offset"] < months
    )
    adjusted_total_free = total_free_cash - total_extra_expenses
    projected_savings = base_savings_goal * months

    total_days = months * 30
    daily_budget = adjusted_total_free / total_days if total_days > 0 else 0

    return {
        "total_free": round(adjusted_total_free, 2),
        "daily_budget": round(daily_budget, 2),
        "projected_savings": round(projected_savings, 2)
    }

