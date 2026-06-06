from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# データベースに4つのテーブル（weights, ingredients, recipes, meal_histories）を自動生成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# データベースの窓口
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "完璧な状態のダイエットアプリ、第一形態が起動しました！"}

# ========================================
# 1. Weight (体重管理)
# ========================================
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    db_weight = models.Weight(date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db)):
    return db.query(models.Weight).all()

# ========================================
# 2. Ingredient (食材マスター)
# ========================================
@app.post("/ingredients/", response_model=schemas.IngredientResponse)
def create_ingredient(ingredient_data: schemas.IngredientCreate, db: Session = Depends(get_db)):
    db_ingredient = models.Ingredient(
        name=ingredient_data.name,
        calories=ingredient_data.calories,
        protein=ingredient_data.protein,
        fat=ingredient_data.fat,
        carbs=ingredient_data.carbs
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).all()

# ========================================
# 3. Recipe (レシピマスター)
# ========================================
@app.post("/recipes/", response_model=schemas.RecipeResponse)
def create_recipe(recipe_data: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(title=recipe_data.title, instructions=recipe_data.instructions)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(db: Session = Depends(get_db)):
    return db.query(models.Recipe).all()

# ========================================
# 4. MealHistory (食事履歴)
# ========================================
@app.post("/meal_histories/", response_model=schemas.MealHistoryResponse)
def create_meal_history(meal_data: schemas.MealHistoryCreate, db: Session = Depends(get_db)):
    db_meal = models.MealHistory(
        date=meal_data.date,
        name=meal_data.name,
        amount_g=meal_data.amount_g,
        calories=meal_data.calories,
        protein=meal_data.protein,
        fat=meal_data.fat,
        carbs=meal_data.carbs
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@app.get("/meal_histories/", response_model=list[schemas.MealHistoryResponse])
def read_meal_histories(db: Session = Depends(get_db)):
    return db.query(models.MealHistory).all