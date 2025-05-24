# forecast/models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.models import Base


class ForecastScenario(Base):
    __tablename__ = "forecast_scenarios"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    months = Column(Integer, nullable=False)  # 1, 3, 6, or 12
    income_changes = Column(Float, default=0.0)
    fixed_changes = Column(Float, default=0.0)
    extra_expenses = Column(JSON, default=[])  # List of {name, amount, month_offset}

    projected_savings = Column(Float)
    daily_budget = Column(Float)
    total_free = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="forecast_scenarios")
