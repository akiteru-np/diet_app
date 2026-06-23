from sqlalchemy import Column, Integer, Float, Date, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# 👤 1. ユーザーテーブル (Supabase Auth連携用)
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True) # UUID
    email = Column(String, unique=True, index=True)

# 2. Weight テーブル
class Weight(Base):
    __tablename__ = "weights"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE")) # ✨追加
    date = Column(Date, index=True)
    weight = Column(Float)

# 3. Ingredient テーブル
class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    # ✨ nullable=True で「全員共通の公式食材」と「ユーザー独自の食材」を分けられる設計に
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) 
    name = Column(String, index=True)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)
    unit = Column(String, default="g")
    recipes = relationship("RecipeIngredient", back_populates="ingredient")

# 4. Recipe テーブル
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE")) # ✨追加
    title = Column(String, index=True)
    instructions = Column(Text)
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

# 4.5 RecipeIngredient 中間テーブル
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"))
    amount = Column(Float)
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")

# 5. MealHistory テーブル
class MealHistory(Base):
    __tablename__ = "meal_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE")) # ✨追加
    date = Column(Date, index=True)
    name = Column(String)
    amount_g = Column(Float)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)

# 6. Goal テーブル
class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True) # ✨追加
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)