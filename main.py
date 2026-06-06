from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# データベース作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# データベースの「窓口」を開け閉めする係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "はじめてのAPIが動きました！ダイエットアプリ開発スタート！"}

# ----------------------------------------
# ここからCRUD機能（体重アプリのメイン機能！）
# ----------------------------------------

# 1. データを入れる（Create: POSTメソッド）
@app.post("/weights/", response_model=schemas.WeightResponse)
def create_weight(weight_data: schemas.WeightCreate, db: Session = Depends(get_db)):
    # 注文票(weight_data)をもとに、DB保存用のデータを作る
    db_weight = models.Weight(date=weight_data.date, weight=weight_data.weight)
    db.add(db_weight)  # 冷蔵庫（DB）に入れる準備
    db.commit()        # 冷蔵庫の扉を閉めて確定！
    db.refresh(db_weight) # 自動で付いたIDなどを最新の状態に更新
    return db_weight

# 2. データを見る（Read: GETメソッド）
@app.get("/weights/", response_model=list[schemas.WeightResponse])
def read_weights(db: Session = Depends(get_db)):
    # テーブルの中身を全部ください、という命令
    weights = db.query(models.Weight).all()
    return weights