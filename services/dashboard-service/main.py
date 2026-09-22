import os
import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

from security import get_current_user_id


WORKOUT_SERVICE_URL = os.getenv(
    "WORKOUT_SERVICE_URL",
    "http://workout-service:8000",
)
MEAL_SERVICE_URL = os.getenv(
    "MEAL_SERVICE_URL",
    "http://meal-service:8000",
)
AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL",
    "http://auth-service:8000",
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard-service")


app = FastAPI(title="Dashboard Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "dashboard-service",
    }


async def fetch_upstream(
    client: httpx.AsyncClient,
    service_name: str,
    url: str,
    params: dict | None = None,
):
    """
    Call an upstream service without allowing that dependency
    to crash the entire dashboard request.
    """

    try:
        response = await client.get(url, params=params)

        if response.status_code == 200:
            return {
                "available": True,
                "status_code": response.status_code,
                "data": response.json(),
                "error": None,
            }

        logger.warning(
            "Upstream service %s returned HTTP %s",
            service_name,
            response.status_code,
        )

        return {
            "available": False,
            "status_code": response.status_code,
            "data": None,
            "error": f"HTTP {response.status_code}",
        }

    except httpx.RequestError as exc:
        logger.error(
            "Upstream service %s unavailable: %s",
            service_name,
            exc,
        )

        return {
            "available": False,
            "status_code": None,
            "data": None,
            "error": str(exc),
        }


@app.get("/dashboard")
async def dashboard(
    user_id: int = Depends(get_current_user_id),
):
    """
    Fan out to auth, workout and meal services.

    Auth is a critical dependency.
    Workout and meal services support graceful degradation.
    """

    async with httpx.AsyncClient(timeout=10.0) as client:
        user_result, workout_result, meal_result = await asyncio.gather(
            fetch_upstream(
                client,
                "auth-service",
                f"{AUTH_SERVICE_URL}/users/{user_id}",
            ),
            fetch_upstream(
                client,
                "workout-service",
                f"{WORKOUT_SERVICE_URL}/workouts/internal/summary",
                params={"user_id": user_id},
            ),
            fetch_upstream(
                client,
                "meal-service",
                f"{MEAL_SERVICE_URL}/meals/internal/summary",
                params={"user_id": user_id},
            ),
        )

    # Auth/user data is required to construct the dashboard.
    if not user_result["available"]:
        if user_result["status_code"] == 404:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        raise HTTPException(
            status_code=503,
            detail="User service unavailable",
        )

    user = user_result["data"]

    workout_available = workout_result["available"]
    meal_available = meal_result["available"]

    workouts = workout_result["data"] or {}
    meals = meal_result["data"] or {}

    calories_consumed = (
        meals.get("today_calories", 0)
        if meal_available
        else None
    )

    calories_burned = (
        workouts.get("today_calories_burned", 0)
        if workout_available
        else None
    )

    net_calories = (
        calories_consumed - calories_burned
        if calories_consumed is not None
        and calories_burned is not None
        else None
    )

    return {
        "user": user,

        "service_status": {
            "auth": {
                "available": True,
            },
            "workout": {
                "available": workout_available,
            },
            "meal": {
                "available": meal_available,
            },
        },

        "today": {
            "calories_consumed": calories_consumed,
            "calories_burned": calories_burned,
            "net_calories": net_calories,

            "protein": (
                meals.get("today_protein", 0)
                if meal_available
                else None
            ),

            "carbs": (
                meals.get("today_carbs", 0)
                if meal_available
                else None
            ),

            "fat": (
                meals.get("today_fat", 0)
                if meal_available
                else None
            ),

            "workout_minutes": (
                workouts.get("today_minutes", 0)
                if workout_available
                else None
            ),

            "workouts": (
                workouts.get("today_workouts", [])
                if workout_available
                else []
            ),

            "meals": (
                meals.get("today_meals", [])
                if meal_available
                else []
            ),
        },

        "week": {
            "calories_consumed": (
                meals.get("week_calories", 0)
                if meal_available
                else None
            ),

            "calories_burned": (
                workouts.get("week_calories_burned", 0)
                if workout_available
                else None
            ),

            "workouts": (
                workouts.get("week_workouts", 0)
                if workout_available
                else None
            ),

            "meals": (
                meals.get("week_meals", 0)
                if meal_available
                else None
            ),
        },

        "totals": {
            "workouts": (
                workouts.get("total_workouts", 0)
                if workout_available
                else None
            ),

            "meals": (
                meals.get("total_meals", 0)
                if meal_available
                else None
            ),
        },

        "recent_workouts": (
            workouts.get("recent", [])
            if workout_available
            else []
        ),

        "recent_meals": (
            meals.get("recent", [])
            if meal_available
            else []
        ),
    }
