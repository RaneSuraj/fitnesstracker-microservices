from pydantic import BaseModel
from typing import Literal


class BMIRequest(BaseModel):
    weight: float  # kg
    height: float  # cm


class BMIResponse(BaseModel):
    weight: float
    height: float
    bmi: float
    category: str
    category_color: str
    recommendation: str
    health_status: str


class CalorieRequest(BaseModel):
    age: int
    gender: Literal["male", "female"]
    weight: float  # kg
    height: float  # cm
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]
    goal: Literal["lose", "maintain", "gain"]


class CalorieResponse(BaseModel):
    bmr: float
    tdee: float
    daily_calories: float
    goal_description: str
    protein_grams: float
    carbs_grams: float
    fat_grams: float
