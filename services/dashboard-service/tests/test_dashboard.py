import pytest
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def override_authentication():
    """
    Avoid generating a real JWT for dashboard unit tests.
    Authentication itself belongs to auth/security tests.
    """

    main.app.dependency_overrides[main.get_current_user_id] = lambda: 1

    yield

    main.app.dependency_overrides.clear()


def healthy_user():
    return {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
    }


def healthy_workout_summary():
    return {
        "today_calories_burned": 400,
        "today_minutes": 45,
        "today_workouts": [],
        "week_calories_burned": 1200,
        "week_workouts": 3,
        "total_workouts": 10,
        "recent": [
            {
                "title": "Running",
                "workout_date": "2026-09-22",
                "calories_burned": 400,
            }
        ],
    }


def healthy_meal_summary():
    return {
        "today_calories": 1800,
        "today_protein": 100,
        "today_carbs": 200,
        "today_fat": 60,
        "today_meals": [],
        "week_calories": 10000,
        "week_meals": 18,
        "total_meals": 50,
        "recent": [
            {
                "name": "Lunch",
                "meal_date": "2026-09-22",
                "calories": 650,
            }
        ],
    }


def available(data):
    return {
        "available": True,
        "status_code": 200,
        "data": data,
        "error": None,
    }


def unavailable(error="Service unavailable"):
    return {
        "available": False,
        "status_code": None,
        "data": None,
        "error": error,
    }


def test_dashboard_when_all_dependencies_are_available(monkeypatch):

    async def fake_fetch_upstream(
        http_client,
        service_name,
        url,
        params=None,
    ):
        if service_name == "auth-service":
            return available(healthy_user())

        if service_name == "workout-service":
            return available(healthy_workout_summary())

        if service_name == "meal-service":
            return available(healthy_meal_summary())

        raise AssertionError(
            f"Unexpected service called: {service_name}"
        )

    monkeypatch.setattr(
        main,
        "fetch_upstream",
        fake_fetch_upstream,
    )

    response = client.get("/dashboard")

    assert response.status_code == 200

    data = response.json()

    assert data["service_status"]["auth"]["available"] is True
    assert data["service_status"]["workout"]["available"] is True
    assert data["service_status"]["meal"]["available"] is True

    assert data["today"]["calories_consumed"] == 1800
    assert data["today"]["calories_burned"] == 400
    assert data["today"]["net_calories"] == 1400
    assert data["today"]["workout_minutes"] == 45


def test_dashboard_gracefully_degrades_when_workout_is_unavailable(
    monkeypatch,
):

    async def fake_fetch_upstream(
        http_client,
        service_name,
        url,
        params=None,
    ):
        if service_name == "auth-service":
            return available(healthy_user())

        if service_name == "workout-service":
            return unavailable(
                "workout-service unavailable"
            )

        if service_name == "meal-service":
            return available(healthy_meal_summary())

        raise AssertionError(
            f"Unexpected service called: {service_name}"
        )

    monkeypatch.setattr(
        main,
        "fetch_upstream",
        fake_fetch_upstream,
    )

    response = client.get("/dashboard")

    #
    # Most important FIT-3 assertion:
    #
    assert response.status_code == 200

    data = response.json()

    assert data["service_status"]["auth"]["available"] is True
    assert data["service_status"]["workout"]["available"] is False
    assert data["service_status"]["meal"]["available"] is True

    #
    # Healthy Meal service data must survive.
    #
    assert data["today"]["calories_consumed"] == 1800
    assert data["today"]["protein"] == 100

    #
    # Unavailable workout information must NOT pretend
    # to be valid zero values.
    #
    assert data["today"]["calories_burned"] is None
    assert data["today"]["workout_minutes"] is None
    assert data["today"]["net_calories"] is None

    assert data["recent_workouts"] == []

    #
    # Meal data must remain usable.
    #
    assert len(data["recent_meals"]) == 1
    assert data["recent_meals"][0]["name"] == "Lunch"


def test_dashboard_returns_503_when_auth_service_is_unavailable(
    monkeypatch,
):

    async def fake_fetch_upstream(
        http_client,
        service_name,
        url,
        params=None,
    ):
        if service_name == "auth-service":
            return unavailable(
                "auth-service unavailable"
            )

        if service_name == "workout-service":
            return available(healthy_workout_summary())

        if service_name == "meal-service":
            return available(healthy_meal_summary())

        raise AssertionError(
            f"Unexpected service called: {service_name}"
        )

    monkeypatch.setattr(
        main,
        "fetch_upstream",
        fake_fetch_upstream,
    )

    response = client.get("/dashboard")

    assert response.status_code == 503
    assert response.json()["detail"] == "User service unavailable"
