from sqlalchemy import Column, Integer, Float, Date, String
from database import Base

# --- 体重テーブル ---
class Weight(Base):
    __tablename__ = "weights"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    weight = Column(Float)

# --- 食事（Meal）テーブル ---
class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    name = Column(String, index=True) 
    amount_g = Column(Float)          # 👈 約束のグラム数！
    calories = Column(Float)          
    protein = Column(Float)           
    fat = Column(Float)               
    carbs = Column(Float)