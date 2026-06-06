from sqlalchemy import Column, Integer, Float, Date, String, Text
from database import Base

# 1. Weight テーブル: 体重の推移を記録する箱
class Weight(Base):
    __tablename__ = "weights"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    weight = Column(Float)

# 2. Ingredient テーブル: 食材のマスターデータを保管する箱
class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)    # 食材名（例：鶏むね肉）
    calories = Column(Float)             # カロリー
    protein = Column(Float)              # タンパク質
    fat = Column(Float)                  # 脂質
    carbs = Column(Float)                # 炭水化物

# 3. Recipe テーブル: レシピのタイトルや作り方を保管する箱
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)   # レシピ名
    instructions = Column(Text)          # 作り方の手順など

# 4. MealHistory テーブル: いつ、何を食べて、どれくらい摂取したかを記録する箱
class MealHistory(Base):
    __tablename__ = "meal_histories"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)      # 食べた日
    name = Column(String)                # 食べたもの（レシピ名や食材名）
    amount_g = Column(Float)             # 食べた量（グラム）
    calories = Column(Float)             # 摂取カロリー
    protein = Column(Float)              # 摂取タンパク質
    fat = Column(Float)                  # 摂取脂質
    carbs = Column(Float)                # 摂取炭水化物