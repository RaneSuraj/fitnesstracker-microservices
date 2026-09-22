from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from security import get_current_user_id

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Workout Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "workout-service"}


@app.get("/exercise-options")
def exercise_options():
    return schemas.EXERCISE_OPTIONS


@app.get("/workouts", response_model=List[schemas.WorkoutOut])
def list_workouts(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Workout)
        .filter(models.Workout.user_id == user_id)
        .order_by(models.Workout.workout_date.desc())
        .all()
    )


@app.post("/workouts", response_model=schemas.WorkoutOut, status_code=201)
def create_workout(
    payload: schemas.WorkoutCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = models.Workout(user_id=user_id, **payload.dict())
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


@app.get("/workouts/{workout_id}", response_model=schemas.WorkoutOut)
def get_workout(
    workout_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = (
        db.query(models.Workout)
        .filter(models.Workout.id == workout_id, models.Workout.user_id == user_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@app.put("/workouts/{workout_id}", response_model=schemas.WorkoutOut)
def update_workout(
    workout_id: int,
    payload: schemas.WorkoutUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = (
        db.query(models.Workout)
        .filter(models.Workout.id == workout_id, models.Workout.user_id == user_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(workout, field, value)
    db.commit()
    db.refresh(workout)
    return workout


@app.delete("/workouts/{workout_id}", status_code=204)
def delete_workout(
    workout_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = (
        db.query(models.Workout)
        .filter(models.Workout.id == workout_id, models.Workout.user_id == user_id)
        .first()
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(workout)
    db.commit()


@app.get("/workouts/internal/summary", include_in_schema=False)
def internal_summary(user_id: int, db: Session = Depends(get_db)):
    """Called by dashboard-service (service-to-service, trusted network) to aggregate stats."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    workouts = db.query(models.Workout).filter(models.Workout.user_id == user_id).all()
    today_list = [w for w in workouts if w.workout_date == today]
    week_list = [w for w in workouts if w.workout_date >= week_ago]
    return {
        "total_workouts": len(workouts),
        "today_workouts": [schemas.WorkoutOut.from_orm(w).dict() for w in today_list],
        "today_calories_burned": sum(w.calories_burned for w in today_list),
        "today_minutes": sum(w.duration_minutes for w in today_list),
        "week_workouts": len(week_list),
        "week_calories_burned": sum(w.calories_burned for w in week_list),
        "recent": [schemas.WorkoutOut.from_orm(w).dict() for w in workouts[:5]],
    }
