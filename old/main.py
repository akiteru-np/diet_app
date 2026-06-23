import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles # ✨ 画像を読み込むための機能
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional
import jwt
import models, schemas
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✨ アイコンなどを置くstaticフォルダを認識させる
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_JWKS_URL = f"{SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
jwks_client = jwt.PyJWKClient(SUPABASE_JWKS_URL)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> str:
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["ES256"], options={"verify_aud": False})
        user_id = payload.get("sub")
        if not user_id: raise HTTPException(status_code=401, detail="無効なトークンです")
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            user = models.User(id=user_id, email=payload.get("email", ""))
            db.add(user); db.commit()
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。再ログインしてください。")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"認証に失敗しました: {str(e)}")

@app.get("/auth/config")
def get_auth_config():
    return {"supabase_url": SUPABASE_URL, "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", "")}

@app.get("/", response_class=HTMLResponse)
@app.head("/")
def read_root():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(path, "r", encoding="utf-8") as f: return f.read()

@app.get("/tags/", response_model=list[str])
def read_tags(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    tags = db.query(models.Tag).all()
    return [t.name for t in tags]

# ── 以下、前回と同じAPI群（Weights, Ingredients, Recipes, Meals, Goals） ──
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    existing = db.query(models.Weight).filter(models.Weight.user_id == user_id, models.Weight.date == weight_data.date).first()
    if existing:
        existing.weight = weight_data.weight
        db.commit(); db.refresh(existing); return existing
    db_weight = models.Weight(user_id=user_id, date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight); db.commit(); db.refresh(db_weight); return db_weight

@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return db.query(models.Weight).filter(models.Weight.user_id == user_id).order_by(models.Weight.date).all()

@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id, models.Weight.user_id == user_id).first()
    if not db_weight: raise HTTPException(status_code=404)
    db.delete(db_weight); db.commit(); return {"status": "success"}

@app.post("/ingredients/", response_model=schemas.IngredientResponse)
def create_ingredient(ingredient_data: schemas.IngredientCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_ingredient = models.Ingredient(user_id=user_id, **ingredient_data.dict())
    db.add(db_ingredient); db.commit(); db.refresh(db_ingredient); return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return db.query(models.Ingredient).all()

@app.delete("/ingredients/{ingredient_id}")
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not db_ingredient: raise HTTPException(status_code=404)
    db.delete(db_ingredient); db.commit(); return {"status": "success"}

def calc_recipe_totals(r):
    total_cal = total_p = total_f = total_c = 0.0
    for ri in r.ingredients:
        ing = ri.ingredient
        if not ing: continue
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
    db.add(db_recipe); db.commit(); db.refresh(db_recipe)
    for ing_part in recipe_data.ingredients:
        db_ri = models.RecipeIngredient(recipe_id=db_recipe.id, ingredient_id=ing_part.ingredient_id, amount=ing_part.amount)
        db.add(db_ri)
    unique_tag_names = list(set([t.strip() for t in recipe_data.tags if t.strip()]))
    for tag_name in unique_tag_names:
        if tag_name.startswith("#"): tag_name = tag_name[1:]
        tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not tag:
            tag = models.Tag(name=tag_name)
            db.add(tag); db.commit(); db.refresh(tag)
        db_recipe.tags.append(tag)
    db.commit(); db.refresh(db_recipe); return calc_recipe_totals(db_recipe)

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(
    title: Optional[str] = Query(None), ingredient_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None), max_cal: Optional[float] = Query(None),
    min_p: Optional[float] = Query(None), max_f: Optional[float] = Query(None),
    max_c: Optional[float] = Query(None), db: Session = Depends(get_db), user_id: str = Depends(get_current_user)
):
    query = db.query(models.Recipe)
    if title: query = query.filter(models.Recipe.title.contains(title))
    if ingredient_id: query = query.join(models.Recipe.ingredients).filter(models.RecipeIngredient.ingredient_id == ingredient_id)
    if tag: query = query.join(models.Recipe.tags).filter(models.Tag.name == tag)
    recipes = query.all()
    calculated = [calc_recipe_totals(r) for r in recipes]
    if max_cal is not None: calculated = [r for r in calculated if r.total_calories <= max_cal]
    if min_p is not None: calculated = [r for r in calculated if r.total_protein >= min_p]
    if max_f is not None: calculated = [r for r in calculated if r.total_fat <= max_f]
    if max_c is not None: calculated = [r for r in calculated if r.total_carbs <= max_c]
    return calculated

@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not db_recipe: raise HTTPException(status_code=404)
    db.delete(db_recipe); db.commit(); return {"status": "success"}

@app.post("/meal_histories/", response_model=schemas.MealHistoryResponse)
def create_meal_history(meal_data: schemas.MealHistoryCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_meal = models.MealHistory(user_id=user_id, **meal_data.dict())
    db.add(db_meal); db.commit(); db.refresh(db_meal); return db_meal

@app.get("/meal_histories/", response_model=list[schemas.MealHistoryResponse])
def read_meal_histories(date: Optional[str] = Query(None), db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    q = db.query(models.MealHistory).filter(models.MealHistory.user_id == user_id)
    if date: q = q.filter(models.MealHistory.date == date)
    return q.order_by(models.MealHistory.id).all()

@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    db_meal = db.query(models.MealHistory).filter(models.MealHistory.id == meal_id, models.MealHistory.user_id == user_id).first()
    if not db_meal: raise HTTPException(status_code=404)
    db.delete(db_meal); db.commit(); return {"status": "success"}

@app.get("/goals/", response_model=Optional[schemas.GoalResponse])
def read_goal(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return db.query(models.Goal).filter(models.Goal.user_id == user_id).first()

@app.post("/goals/", response_model=schemas.GoalResponse)
def upsert_goal(goal_data: schemas.GoalCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    existing = db.query(models.Goal).filter(models.Goal.user_id == user_id).first()
    if existing:
        for key, value in goal_data.dict().items(): setattr(existing, key, value)
        db.commit(); db.refresh(existing); return existing
    db_goal = models.Goal(user_id=user_id, **goal_data.dict())
    db.add(db_goal); db.commit(); db.refresh(db_goal); return db_goal