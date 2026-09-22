from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import schemas

app = FastAPI(title="Calculator Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENT = {
    "lose": -500,
    "maintain": 0,
    "gain": 500,
}

GOAL_DESCRIPTIONS = {
    "lose": "A ~500 kcal/day deficit for steady, sustainable weight loss (~0.5 kg/week).",
    "maintain": "Calories set to maintain your current weight.",
    "gain": "A ~500 kcal/day surplus to support muscle gain.",
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "calculator-service"}


@app.post("/bmi", response_model=schemas.BMIResponse)
def calculate_bmi(payload: schemas.BMIRequest):
    height_m = payload.height / 100
    bmi = round(payload.weight / (height_m ** 2), 1)

    if bmi < 18.5:
        category, color = "Underweight", "#378ADD"
        recommendation = "Consider increasing calorie intake with nutrient-dense foods and consult a doctor."
        status_text = "Below healthy range"
    elif bmi < 25:
        category, color = "Normal weight", "#639922"
        recommendation = "Great! Maintain your current balanced diet and activity level."
        status_text = "Healthy range"
    elif bmi < 30:
        category, color = "Overweight", "#BA7517"
        recommendation = "A modest calorie deficit and regular activity can help move toward a healthy range."
        status_text = "Above healthy range"
    else:
        category, color = "Obese", "#A32D2D"
        recommendation = "Consider consulting a healthcare provider for a personalized plan."
        status_text = "Well above healthy range"

    return schemas.BMIResponse(
        weight=payload.weight,
        height=payload.height,
        bmi=bmi,
        category=category,
        category_color=color,
        recommendation=recommendation,
        health_status=status_text,
    )


@app.post("/calorie", response_model=schemas.CalorieResponse)
def calculate_calorie(payload: schemas.CalorieRequest):
    # Mifflin-St Jeor equation
    if payload.gender == "male":
        bmr = 10 * payload.weight + 6.25 * payload.height - 5 * payload.age + 5
    else:
        bmr = 10 * payload.weight + 6.25 * payload.height - 5 * payload.age - 161

    tdee = bmr * ACTIVITY_MULTIPLIERS[payload.activity_level]
    daily_calories = tdee + GOAL_ADJUSTMENT[payload.goal]

    # Macro split: 30% protein / 40% carbs / 30% fat (kcal -> grams)
    protein_grams = round((daily_calories * 0.30) / 4, 1)
    carbs_grams = round((daily_calories * 0.40) / 4, 1)
    fat_grams = round((daily_calories * 0.30) / 9, 1)

    return schemas.CalorieResponse(
        bmr=round(bmr, 1),
        tdee=round(tdee, 1),
        daily_calories=round(daily_calories, 1),
        goal_description=GOAL_DESCRIPTIONS[payload.goal],
        protein_grams=protein_grams,
        carbs_grams=carbs_grams,
        fat_grams=fat_grams,
    )
