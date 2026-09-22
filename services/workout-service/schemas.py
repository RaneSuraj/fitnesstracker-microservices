from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class WorkoutCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    duration_minutes: int
    calories_burned: int
    icon: Optional[str] = None
    workout_date: date


class WorkoutUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    duration_minutes: Optional[int] = None
    calories_burned: Optional[int] = None
    icon: Optional[str] = None
    workout_date: Optional[date] = None


class WorkoutOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    type: str
    duration_minutes: int
    calories_burned: int
    icon: Optional[str] = None
    workout_date: date
    created_at: datetime

    class Config:
        from_attributes = True


# Static reference data for the "Add workout" form
EXERCISE_OPTIONS = [
    {"name": "Running", "icon": "ti-run", "type": "Cardio", "calories_per_hour": 600},
    {"name": "Cycling", "icon": "ti-bike", "type": "Cardio", "calories_per_hour": 500},
    {"name": "Swimming", "icon": "ti-swimming", "type": "Cardio", "calories_per_hour": 550},
    {"name": "Weight training", "icon": "ti-barbell", "type": "Strength", "calories_per_hour": 400},
    {"name": "Yoga", "icon": "ti-yoga", "type": "Flexibility", "calories_per_hour": 250},
    {"name": "HIIT", "icon": "ti-bolt", "type": "Cardio", "calories_per_hour": 700},
    {"name": "Walking", "icon": "ti-walk", "type": "Cardio", "calories_per_hour": 300},
]
