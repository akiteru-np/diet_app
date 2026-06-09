from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import models, schemas
from database import engine, SessionLocal

# データベースにテーブルを自動生成・更新
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🔽 templatesフォルダの中のHTMLを使う準備！
templates = Jinja2Templates(directory="templates")

# データベースの窓口
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================================
# 🏠 案内係（スッキリ分離版！）
# ========================================
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # ✨ 最新ルール！名前をハッキリ指定して渡すことで誤解を完全ブロック！
    return templates.TemplateResponse(request=request, name="index.html")
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

# --- 🧹 体重の削除API（追加！） ---
@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if not db_weight:
        raise HTTPException(status_code=404, detail="Weight not found")
    db.delete(db_weight)
    db.commit()
    return {"status": "success"}

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
        carbs=ingredient_data.carbs,
        unit=ingredient_data.unit
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).all()

# ========================================
# 3. Recipe (レシピマスター：✨リレーショナル自動計算版)
# ========================================
@app.post("/recipes/", response_model=schemas.RecipeResponse)
def create_recipe(recipe_data: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(title=recipe_data.title, instructions=recipe_data.instructions)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)

    for ing_part in recipe_data.ingredients:
        db_ri = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=ing_part.ingredient_id,
            amount=ing_part.amount
        )
        db.add(db_ri)
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
    return