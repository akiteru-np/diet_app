from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# データベース作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# データベースの「窓口」
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "はじめてのAPIが動きました！ダイエットアプリ開発スタート！"}

# --- C (Create: 登録) ---
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    db_weight = models.Weight(date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight

# --- R (Read: 読み取り) ---
@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db)):
    weights = db.query(models.Weight).all()
    return weights

# ----------------------------------------
# 👇 今回新しく追加した機能（U と D） 👇
# ----------------------------------------

# --- U (Update: 修正) ---
@app.put("/weights/{weight_id}", response_model=schemas.WeightResponse)
def update_weight(weight_id: int, weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    # 1. まずは修正したいデータを「背番号（ID）」で探す
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if db_weight is None:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    # 2. 見つかったら、新しい値で上書きして保存する
    db_weight.date = weight_data.date
    db_weight.weight = weight_data.weight
    db.commit()
    db.refresh(db_weight)
    return db_weight

# --- D (Delete: 削除) ---
@app.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    # 1. まずは消したいデータを「背番号（ID）」で探す
    db_weight = db.query(models.Weight).filter(models.Weight.id == weight_id).first()
    if db_weight is None:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    
    # 2. 見つかったら削除する
    db.delete(db_weight)
    db.commit()
    return {"message": "削除が完了しました"}