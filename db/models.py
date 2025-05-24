from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=True)  # Был Integer
    monthly_savings = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)

    from sqlalchemy.orm import relationship
    forecast_scenarios = relationship("ForecastScenario", back_populates="user", cascade="all, delete-orphan")

class FixedExpense(Base):
    __tablename__ = 'fixed_expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)  # Был Integer

class DailyExpense(Base):
    __tablename__ = 'daily_expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("expense_categories.id"))  # ← 🆕 добавь это
    amount = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)

class SavingsBalance(Base):
    __tablename__ = 'savings_balance'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    amount = Column(Float, default=0.0)

class MonthlyBudget(Base):
    __tablename__ = 'monthly_budgets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    month_start = Column(DateTime, nullable=False)
    income = Column(Float, nullable=False)
    fixed = Column(Float, nullable=False)
    savings_goal = Column(Float, nullable=False)
    remaining = Column(Float, nullable=False)
    coefficient = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class MonthlyBudgetAdjustment(Base):
    __tablename__ = "monthly_budget_adjustments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    month = Column(DateTime, nullable=False)  # начало месяца
    source = Column(String, nullable=False)  # 'income', 'fixed_expense', 'savings'
    type = Column(String, nullable=False)  # 'add' или 'subtract'
    amount = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    apply_permanently = Column(Integer, default=0)  # 0 = нет, 1 = да
    processed = Column(Integer, default=0)  # 0 = нет, 1 = да
    created_at = Column(DateTime, default=datetime.utcnow)

