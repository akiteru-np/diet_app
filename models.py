from sqlalchemy import Column, Integer, Float, Date, String, Text, ForeignKey
from sqlalchemy.orm import relationship
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
    calories = Column(Float)             # 100g(または1個)あたりのカロリー
    protein = Column(Float)              # 100g(または1個)あたりのタンパク質
    fat = Column(Float)                  # 100g(または1個)あたりの脂質
    carbs = Column(Float)                # 100g(wagon1個)あたりの炭水化物
    unit = Column(String, default="g")   # ✨追加：単位の識別（"g"ベースか、"個"ベースか）

    # レシピ中間テーブルとの結びつき
    recipes = relationship("RecipeIngredient", back_populates="ingredient")

# 3. Recipe テーブル: レシピのタイトルや作り方を保管する箱
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)   # レシピ名
    instructions = Column(Text)          # 作り方の手順など

    # ✨紐付け：このレシピに含まれる食材たち（中間テーブル経由）
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

# ⭐️ 3.5 RecipeIngredient テーブル: 【新設】レシピと食材を繋ぐ中間テーブル
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"))
    amount = Column(Float)               # そのレシピで使う数量（g数や個数）

    # 互いのデータに一瞬でアクセスするためのリレーション
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")

# 4. MealHistory テーブル: いつ、何を食べて、どれくらい摂取したかを記録する箱
class MealHistory(Base):
    __shadow__ = "meal_histories"
    __tablename__ = "meal_histories"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)      # 食べた日
    name = Column(String)                # 食べたもの（レシピ名や食材名）
    amount_g = Column(Float)             # 食べた量（グラムまたは個数換算）
    calories = Column(Float)             # 実際に摂取したカロリー（自動計算値が入る）
    protein = Column(Float)              # 実際に摂取したタンパク質
    fat = Column(Float)                  # 実際に摂取した脂質
    carbs = Column(Float)                # 実際に摂取した炭水化物