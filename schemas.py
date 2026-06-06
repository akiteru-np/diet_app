from pydantic import BaseModel
from datetime import date

# 1. 登録する時（Create）の注文票ルール
class WeightCreate(BaseModel):
    date: date      # 日付（例: 2026-06-06）
    weight: float   # 体重（例: 65.5）

# 2. データを返す時（Read）のルール
class WeightResponse(WeightCreate):
    id: int         # データベースが自動でつけた背番号（ID）も一緒に返す

    class Config:
        from_attributes = True  # DBのデータをうまく変換するための魔法のおまじない