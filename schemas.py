from pydantic import BaseModel
from datetime import date

# 1. Weight (体重) の注文票
class WeightCreate(BaseModel):
    date: date
    weight: float

class WeightResponse(WeightCreate):
    id: int
    class Config:
        from_attributes = True

# 2. Ingredient (食材) の注文票
class IngredientCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float

class IngredientResponse(IngredientCreate):
    id: int
    class Config:
        from_attributes = True

# 3. Recipe (レシピ) の注文票
class RecipeCreate(BaseModel):
    title: str
    instructions: str

class RecipeResponse(RecipeCreate):
    id: int
    class Config:
        from_attributes = True

# 4. MealHistory (食事履歴) の注文票
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
    class Config:
        from_attributes = True