from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    meal_type = Column(String, nullable=False)     # Breakfast, Lunch, Dinner, Snack
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False, default=0)
    carbs = Column(Float, nullable=False, default=0)
    fat = Column(Float, nullable=False, default=0)
    icon = Column(String, nullable=True)
    meal_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
