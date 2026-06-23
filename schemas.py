from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class WeightCreate(BaseModel):
    date: date
    weight: float

class WeightResponse(WeightCreate):
    id: int
    user_id: str
    class Config:
        from_attributes = True

class IngredientCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    unit: str = "g"

class IngredientResponse(IngredientCreate):
    id: int
    user_id: Optional[str] = None
    class Config:
        from_attributes = True

class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    amount: float

class RecipeIngredientResponse(BaseModel):
    id: int
    ingredient_id: int
    amount: float
    ingredient: IngredientResponse
    class Config:
        from_attributes = True

class RecipeCreate(BaseModel):
    title: str
    instructions: str
    ingredients: List[RecipeIngredientCreate] = []

class RecipeResponse(BaseModel):
    id: int
    user_id: str
    title: str
    instructions: str
    ingredients: List[RecipeIngredientResponse] = []
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_fat: float = 0.0
    total_carbs: float = 0.0
    class Config:
        from_attributes = True

class MealHistoryCreate(BaseModel):
    date: date
    name: str
    amount_g: float
    calories: float
    protein: float
    fat: float
    carbs: float

class MealHistoryResponse(MealHistoryCreate):
    id: int
    user_id: str
    class Config:
        from_attributes = True

class GoalCreate(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float

class GoalResponse(GoalCreate):
    id: int
    user_id: str
    class Config:
        from_attributes = True