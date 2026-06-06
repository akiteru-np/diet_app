from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# データベース作成（ここで新しいMealテーブルも作られます！）
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "はじめてのAPIが動きました！ダイエットアプリ開発スタート！"}

# ========================================
# ⚖️ 体重（Weight）の機能
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

@app.put("/weights/{weight_id}", response_model=schemas.WeightResponse)
def update_weight(weight_id: int, weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if db_weight is None:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    db_weight.date = weight_data.date
    db_weight.weight = weight_data.weight
    db.commit()
    db.refresh(db_weight)
    return db_weight

@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if db_weight is None:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    db.delete(db_weight)
    db.commit()
    return {"message": "削除が完了しました"}


# ========================================
# 🍱 食事（Meal）の機能（✨NEW✨）
# ========================================
@app.post("/meals/", response_model=schemas.MealResponse)
def create_meal(meal_data: schemas.MealCreate, db: Session = Depends(get_db)):
    # 注文票通りにデータを作って保存！グラム数もバッチリ入ってます。
    db_meal = models.Meal(
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

@app.get("/meals/", response_model=list[schemas.MealResponse])
def read_meals(db: Session = Depends(get_db)):
    return db.query(models.Meal).all()