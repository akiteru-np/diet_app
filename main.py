import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
import jwt  # ✨追加：暗号解読ツール
import models, schemas
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBearer() # ✨追加：APIの入り口に立つ警備員

# 環境変数からJWT Secretを取得（設定されていなければエラー防止のダミーを入れる）
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "dummy_secret")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 👑 本物のログイン認証（Supabase JWTトークンの検証）
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> str:
    token = credentials.credentials
    try:
        # Supabaseが発行した「身分証明書」が本物か、秘密の鍵でチェック！
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="無効なトークンです")
            
        # ユーザーがDBに存在するか確認（初めてのログインなら自動的にユーザー登録）
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            user = models.User(id=user_id, email=payload.get("email", ""))
            db.add(user)
            db.commit()
            
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="無効なトークンです")

# ── ルート ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.head("/")
def read_root():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ── 1. Weight ──────────────────────────────────────
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    existing = db.query(models.Weight).filter(models.Weight.user_id == user_id, models.Weight.date == weight_data.date).first()
    if existing:
        existing.weight = weight_data.weight
        db.commit()
        db.refresh(existing)
        return existing
    db_weight = models.Weight(user_id=user_id, date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return db.query(models.Weight).filter(models.Weight.user_id == user_id).order_by(models.Weight.date).all()

@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id, models.Weight.user_id == user_id).first()
    if not db_weight: raise HTTPException(status_code=404)
    db.delete(db_weight)
    db.commit()
    return {"status": "success"}

# ── 2. Ingredient ──────────────────────────────────
@app.post("/ingredients/", response_model=schemas.IngredientResponse)
def create_ingredient(ingredient_data: schemas.IngredientCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_ingredient = models.Ingredient(user_id=user_id, **ingredient_data.dict())
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    # 共通食材（user_id=None）か、自分の食材かを両方取得
    return db.query(models.Ingredient).filter((models.Ingredient.user_id == user_id) | (models.Ingredient.user_id == None)).all()

@app.delete("/ingredients/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id, models.Ingredient.user_id == user_id).first()
    if not db_ingredient: raise HTTPException(status_code=404, detail="権限がありません")
    db.delete(db_ingredient)
    db.commit()
    return {"status": "success"}

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
    r.total_calories, r.total_protein, r.total_fat, r.total_carbs = total_cal, total_p, total_f, total_c
    return r

@app.post("/recipes/", response_model=schemas.RecipeResponse)
def create_recipe(recipe_data: schemas.RecipeCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_recipe = models.Recipe(user_id=user_id, title=recipe_data.title, instructions=recipe_data.instructions)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    for ing_part in recipe_data.ingredients:
        db_ri = models.RecipeIngredient(recipe_id=db_recipe.id, ingredient_id=ing_part.ingredient_id, amount=ing_part.amount)
        db.add(db_ri)
    db.commit()
    db.refresh(db_recipe)
    return calc_recipe_totals(db_recipe)

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    recipes = db.query(models.Recipe).filter(models.Recipe.user_id == user_id).all()
    return [calc_recipe_totals(r) for r in recipes]

@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id, models.Recipe.user_id == user_id).first()
    if not db_recipe: raise HTTPException(status_code=404)
    db.delete(db_recipe)
    db.commit()
    return {"status": "success"}

# ── 4. MealHistory ─────────────────────────────────
@app.post("/meal_histories/", response_model=schemas.MealHistoryResponse)
def create_meal_history(meal_data: schemas.MealHistoryCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_meal = models.MealHistory(user_id=user_id, **meal_data.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@app.get("/meal_histories/", response_model=list[schemas.MealHistoryResponse])
def read_meal_histories(date: Optional[str] = Query(None), db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    q = db.query(models.MealHistory).filter(models.MealHistory.user_id == user_id)
    if date: q = q.filter(models.MealHistory.date == date)
    return q.order_by(models.MealHistory.id).all()

@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_meal = db.query(models.MealHistory).filter(models.MealHistory.id == meal_id, models.MealHistory.user_id == user_id).first()
    if not db_meal: raise HTTPException(status_code=404)
    db.delete(db_meal)
    db.commit()
    return {"status": "success"}

# ── 5. Goal ────────────────────────────────────────
@app.get("/goals/", response_model=Optional[schemas.GoalResponse])
def read_goal(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return db.query(models.Goal).filter(models.Goal.user_id == user_id).first()

@app.post("/goals/", response_model=schemas.GoalResponse)
def upsert_goal(goal_data: schemas.GoalCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    existing = db.query(models.Goal).filter(models.Goal.user_id == user_id).first()
    if existing:
        for key, value in goal_data.dict().items(): setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    db_goal = models.Goal(user_id=user_id, **goal_data.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal