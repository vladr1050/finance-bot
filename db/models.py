# app/db/models.py

import uuid
from sqlalchemy import func, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    user_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email_confirmed = Column(Boolean, default=False)
    confirmation_token = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=True)
    monthly_savings = Column(Float, default=0)
    created_from = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_premium = Column(Boolean, default=False)
    forecast_scenarios = relationship("ForecastScenario", back_populates="user", cascade="all, delete-orphan")

class FixedExpense(Base):
    __tablename__ = 'fixed_expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)  # Был Integer
    created_at = Column(DateTime, default=datetime.utcnow)

class DailyExpense(Base):
    __tablename__ = 'daily_expenses'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    category_id = Column(Integer, ForeignKey("expense_categories.id"))  # ← 🆕 добавь это
    category = relationship("ExpenseCategory")
    amount = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SavingsBalance(Base):
    __tablename__ = 'savings_balance'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    amount = Column(Float, default=0.0)

class MonthlyBudget(Base):
    __tablename__ = 'monthly_budgets'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    month = Column(DateTime, nullable=False)  # начало месяца
    source = Column(String, nullable=False)  # 'income', 'fixed_expense', 'savings'
    type = Column(String, nullable=False)  # 'add' или 'subtract'
    amount = Column(Float, nullable=False)
    comment = Column(String, nullable=True)
    apply_permanently = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ForecastScenario(Base):
    __tablename__ = "forecast_scenarios"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_uuid"))
    name = Column(String, nullable=False)
    months = Column(Integer, nullable=False)  # 1, 3, 6, or 12
    income_changes = Column(Float, default=0.0)
    fixed_changes = Column(Float, default=0.0)
    extra_expenses = Column(JSONB, default=list)
    projected_savings = Column(Float)
    daily_budget = Column(Float)
    total_free = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="forecast_scenarios")