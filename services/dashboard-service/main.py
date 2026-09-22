import os
import asyncio
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from security import get_current_user_id

WORKOUT_SERVICE_URL = os.getenv("WORKOUT_SERVICE_URL", "http://workout-service:8000")
MEAL_SERVICE_URL = os.getenv("MEAL_SERVICE_URL", "http://meal-service:8000")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")

app = FastAPI(title="Dashboard Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard-service"}


@app.get("/dashboard")
async def dashboard(user_id: int = Depends(get_current_user_id)):
    """Fan-out to workout-service, meal-service and auth-service, then merge the results.
    This is the orchestration layer of the microservices architecture."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            user_resp, workout_resp, meal_resp = await asyncio.gather(
                client.get(f"{AUTH_SERVICE_URL}/users/{user_id}"),
                client.get(f"{WORKOUT_SERVICE_URL}/workouts/internal/summary", params={"user_id": user_id}),
                client.get(f"{MEAL_SERVICE_URL}/meals/internal/summary", params={"user_id": user_id}),
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Upstream service unavailable: {exc}")

    if user_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_resp.json()
    workouts = workout_resp.json() if workout_resp.status_code == 200 else {}
    meals = meal_resp.json() if meal_resp.status_code == 200 else {}

    today_calories_consumed = meals.get("today_calories", 0)
    today_calories_burned = workouts.get("today_calories_burned", 0)

    return {
        "user": user,
        "today": {
            "calories_consumed": today_calories_consumed,
            "calories_burned": today_calories_burned,
            "net_calories": today_calories_consumed - today_calories_burned,
            "protein": meals.get("today_protein", 0),
            "carbs": meals.get("today_carbs", 0),
            "fat": meals.get("today_fat", 0),
            "workout_minutes": workouts.get("today_minutes", 0),
            "workouts": workouts.get("today_workouts", []),
            "meals": meals.get("today_meals", []),
        },
        "week": {
            "calories_consumed": meals.get("week_calories", 0),
            "calories_burned": workouts.get("week_calories_burned", 0),
            "workouts": workouts.get("week_workouts", 0),
            "meals": meals.get("week_meals", 0),
        },
        "totals": {
            "workouts": workouts.get("total_workouts", 0),
            "meals": meals.get("total_meals", 0),
        },
        "recent_workouts": workouts.get("recent", []),
        "recent_meals": meals.get("recent", []),
    }
