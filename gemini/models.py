from sqlalchemy import Column, Integer, Float, Date, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# 1. Weight テーブル
class Weight(Base):
    __tablename__ = "weights"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    weight = Column(Float)

# 2. Ingredient テーブル
class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)
    unit = Column(String, default="g")
    
    recipes = relationship("RecipeIngredient", back_populates="ingredient")

# 3. Recipe テーブル
class Recipe(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    instructions = Column(Text)
    
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")

    # ✨修正：モデル自身にPFCの自動計算能力（プロパティ）を持たせる！
    @property
    def total_calories(self):
        return sum((ri.ingredient.calories or 0) * (ri.amount / 100.0 if ri.ingredient.unit == "g" else ri.amount) for ri in self.ingredients if ri.ingredient)

    @property
    def total_protein(self):
        return sum((ri.ingredient.protein or 0) * (ri.amount / 100.0 if ri.ingredient.unit == "g" else ri.amount) for ri in self.ingredients if ri.ingredient)

    @property
    def total_fat(self):
        return sum((ri.ingredient.fat or 0) * (ri.amount / 100.0 if ri.ingredient.unit == "g" else ri.amount) for ri in self.ingredients if ri.ingredient)

    @property
    def total_carbs(self):
        return sum((ri.ingredient.carbs or 0) * (ri.amount / 100.0 if ri.ingredient.unit == "g" else ri.amount) for ri in self.ingredients if ri.ingredient)

# 3.5 RecipeIngredient テーブル
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id = Column(Integer, ForeignKey("ingredients.id", ondelete="CASCADE"))
    amount = Column(Float)
    
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipes")

# 4. MealHistory テーブル
class MealHistory(Base):
    __tablename__ = "meal_histories"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    name = Column(String)
    amount_g = Column(Float)
    calories = Column(Float)
    protein = Column(Float)
    fat = Column(Float)
    carbs = Column(Float)