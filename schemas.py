from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# 1. Weight (体重) 
class WeightCreate(BaseModel):
    date: date
    weight: float

class WeightResponse(WeightCreate):
    id: int
    class Config:
        from_attributes = True

# 2. Ingredient (食材マスター)
class IngredientCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    unit: str = "g" # ✨追加：単位（"g" または "個"）

class IngredientResponse(IngredientCreate):
    id: int
    class Config:
        from_attributes = True

# ⭐️ 中間テーブル用の注文票（レシピ作成時にパーツとして使う）
class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    amount: float

class RecipeIngredientResponse(BaseModel):
    id: int
    ingredient_id: int
    amount: float
    ingredient: IngredientResponse # 食材の詳細情報も入れ子で返す
    class Config:
        from_attributes = True

# 3. Recipe (レシピマスター)
class RecipeCreate(BaseModel):
    title: str
    instructions: str
    # ✨超重要：レシピ作成時に、使用する食材のIDと分量のリストを一緒に受け取る！
    ingredients: List[RecipeIngredientCreate] = []

class RecipeResponse(BaseModel):
    id: int
    title: str
    instructions: str
    ingredients: List[RecipeIngredientResponse] = []
    
    # ✨魔法の自動計算フィールド：レシピ全体の基準値を算出
    total_calories: float = 0.0
    total_protein: float = 0.0
    total_fat: float = 0.0
    total_carbs: float = 0.0

    class Config:
        from_attributes = True

# 4. MealHistory (食事履歴)
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