from fastapi import FastAPI
import models
from database import engine

# 魔法の命令：設計図（models）をもとに、データベース（エンジン）に実際のテーブルを作らせる！
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "はじめてのAPIが動きました！ダイエットアプリ開発スタート！"}