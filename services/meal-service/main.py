from datetime import date, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from security import get_current_user_id

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meal Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "meal-service"}


@app.get("/meal-options")
def meal_options(meal_type: str | None = None):
    if meal_type:
        return [m for m in schemas.MEAL_OPTIONS if m["meal_type"] == meal_type]
    return schemas.MEAL_OPTIONS


@app.get("/meals", response_model=List[schemas.MealOut])
def list_meals(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Meal)
        .filter(models.Meal.user_id == user_id)
        .order_by(models.Meal.meal_date.desc())
        .all()
    )


@app.post("/meals", response_model=schemas.MealOut, status_code=201)
def create_meal(
    payload: schemas.MealCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    meal = models.Meal(user_id=user_id, **payload.dict())
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


@app.get("/meals/{meal_id}", response_model=schemas.MealOut)
def get_meal(
    meal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    meal = db.query(models.Meal).filter(models.Meal.id == meal_id, models.Meal.user_id == user_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal


@app.put("/meals/{meal_id}", response_model=schemas.MealOut)
def update_meal(
    meal_id: int,
    payload: schemas.MealUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    meal = db.query(models.Meal).filter(models.Meal.id == meal_id, models.Meal.user_id == user_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return meal


@app.delete("/meals/{meal_id}", status_code=204)
def delete_meal(
    meal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    meal = db.query(models.Meal).filter(models.Meal.id == meal_id, models.Meal.user_id == user_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    db.delete(meal)
    db.commit()


@app.get("/meals/internal/summary", include_in_schema=False)
def internal_summary(user_id: int, db: Session = Depends(get_db)):
    """Called by dashboard-service to aggregate stats."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    meals = db.query(models.Meal).filter(models.Meal.user_id == user_id).all()
    today_list = [m for m in meals if m.meal_date == today]
    week_list = [m for m in meals if m.meal_date >= week_ago]
    return {
        "total_meals": len(meals),
        "today_meals": [schemas.MealOut.from_orm(m).dict() for m in today_list],
        "today_calories": sum(m.calories for m in today_list),
        "today_protein": sum(m.protein for m in today_list),
        "today_carbs": sum(m.carbs for m in today_list),
        "today_fat": sum(m.fat for m in today_list),
        "week_meals": len(week_list),
        "week_calories": sum(m.calories for m in week_list),
        "recent": [schemas.MealOut.from_orm(m).dict() for m in meals[:5]],
    }
