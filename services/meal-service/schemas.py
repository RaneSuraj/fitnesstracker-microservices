from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class MealCreate(BaseModel):
    name: str
    description: Optional[str] = None
    meal_type: str
    calories: int
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    icon: Optional[str] = None
    meal_date: date


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    meal_type: Optional[str] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    icon: Optional[str] = None
    meal_date: Optional[date] = None


class MealOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    meal_type: str
    calories: int
    protein: float
    carbs: float
    fat: float
    icon: Optional[str] = None
    meal_date: date
    created_at: datetime

    class Config:
        from_attributes = True


MEAL_OPTIONS = [
    {"name": "Oatmeal with fruit", "icon": "ti-bowl", "meal_type": "Breakfast", "calories": 320, "protein": 10, "carbs": 55, "fat": 6},
    {"name": "Grilled chicken salad", "icon": "ti-salad", "meal_type": "Lunch", "calories": 450, "protein": 40, "carbs": 20, "fat": 18},
    {"name": "Salmon with rice", "icon": "ti-fish", "meal_type": "Dinner", "calories": 600, "protein": 42, "carbs": 55, "fat": 20},
    {"name": "Greek yogurt", "icon": "ti-milk", "meal_type": "Snack", "calories": 150, "protein": 15, "carbs": 12, "fat": 4},
    {"name": "Protein shake", "icon": "ti-glass", "meal_type": "Snack", "calories": 220, "protein": 30, "carbs": 10, "fat": 4},
]
