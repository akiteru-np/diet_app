from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date as date_type
from typing import Optional
import models, schemas
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── ルート ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

# ── 1. Weight ──────────────────────────────────────
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Weight).filter(models.Weight.date == weight_data.date).first()
    if existing:
        # 同日 → 上書き更新
        existing.weight = weight_data.weight
        db.commit()
        db.refresh(existing)
        return existing
    db_weight = models.Weight(date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db)):
    return db.query(models.Weight).order_by(models.Weight.date).all()

@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if not db_weight:
        raise HTTPException(status_code=404, detail="Weight not found")
    db.delete(db_weight)
    db.commit()
    return {"status": "success", "message": f"Weight {weight_id} deleted"}

# ── 2. Ingredient ──────────────────────────────────
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

@app.delete("/ingredients/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    db_ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not db_ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(db_ingredient)
    db.commit()
    return {"status": "success", "message": f"Ingredient {ingredient_id} deleted"}

# ── 3. Recipe ──────────────────────────────────────
def calc_recipe_totals(r):
    total_cal = total_p = total_f = total_c = 0.0
    for ri in r.ingredients:
        ing = ri.ingredient
        factor = ri.amount / 100.0 if ing.unit == "g" else ri.amount
        total_cal += (ing.calories or 0) * factor
        total_p   += (ing.protein  or 0) * factor
        total_f   += (ing.fat      or 0) * factor
        total_c   += (ing.carbs    or 0) * factor
    r.total_calories = total_cal
    r.total_protein  = total_p
    r.total_fat      = total_f
    r.total_carbs    = total_c
    return r

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
    return calc_recipe_totals(db_recipe)

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(db: Session = Depends(get_db)):
    recipes = db.query(models.Recipe).all()
    return [calc_recipe_totals(r) for r in recipes]

@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    db.delete(db_recipe)
    db.commit()
    return {"status": "success", "message": f"Recipe {recipe_id} deleted"}

# ── 4. MealHistory ─────────────────────────────────
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
def read_meal_histories(date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.MealHistory)
    if date:
        q = q.filter(models.MealHistory.date == date)
    return q.order_by(models.MealHistory.id).all()

@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    db_meal = db.query(models.MealHistory).filter(models.MealHistory.id == meal_id).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    db.delete(db_meal)
    db.commit()
    return {"status": "success", "message": f"Meal {meal_id} deleted"}

# ── 5. Goal ────────────────────────────────────────
@app.get("/goals/", response_model=Optional[schemas.GoalResponse])
def read_goal(db: Session = Depends(get_db)):
    return db.query(models.Goal).first()

@app.post("/goals/", response_model=schemas.GoalResponse)
def upsert_goal(goal_data: schemas.GoalCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Goal).first()
    if existing:
        existing.calories = goal_data.calories
        existing.protein  = goal_data.protein
        existing.fat      = goal_data.fat
        existing.carbs    = goal_data.carbs
        db.commit()
        db.refresh(existing)
        return existing
    db_goal = models.Goal(**goal_data.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal
