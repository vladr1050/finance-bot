# forecast/logic.py

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
    """
    Calculate a future budget forecast based on current and projected values.

    Parameters:
        base_income: Current monthly income
        base_fixed_expenses: Current monthly fixed costs
        base_savings_goal: Desired monthly savings
        months: Forecast period in months (1, 3, 6, or 12)
        income_changes: Monthly income change (can be positive or negative)
        fixed_changes: Monthly fixed cost change (can be positive or negative)
        extra_expenses: List of extra costs, each as {"name": str, "amount": float, "month_offset": int}

    Returns:
        Dictionary with total free cash, average daily budget and projected savings
    """

    if extra_expenses is None:
        extra_expenses = []

    # Adjusted monthly values
    monthly_income = base_income + income_changes
    monthly_fixed = base_fixed_expenses + fixed_changes

    # Monthly available amount after fixed + savings
    monthly_free_cash = monthly_income - monthly_fixed - base_savings_goal
    total_free_cash = monthly_free_cash * months

    # Deduct extra planned expenses
    total_extra_expenses = sum(e["amount"] for e in extra_expenses if 0 <= e["month_offset"] < months)
    adjusted_total_free = total_free_cash - total_extra_expenses

    # Total savings
    projected_savings = base_savings_goal * months

    # Average daily budget (for the whole forecast period)
    total_days = months * 30  # rough average
    daily_budget = adjusted_total_free / total_days if total_days > 0 else 0

    return {
        "total_free": round(adjusted_total_free, 2),
        "daily_budget": round(daily_budget, 2),
        "projected_savings": round(projected_savings, 2)
    }
