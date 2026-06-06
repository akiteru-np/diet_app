from pydantic import BaseModel
from datetime import date

# --- Weight (体重) ---
class WeightCreate(BaseModel):
    date: date
    weight: float

class WeightResponse(WeightCreate):
    id: int
    class Config:
        from_attributes = True

# --- Meal (食事) ---
class MealCreate(BaseModel):
    date: date
    name: str           
    amount_g: float     # 👈 約束のグラム数！
    calories: float
    protein: float
    fat: float
    carbs: float

class MealResponse(MealCreate):
    id: int
    class Config:
        from_attributes = True