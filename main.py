from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal

# データベースに4つのテーブルを自動生成
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# データベースの窓口
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========================================
# 🏠 案内係（完璧な体重ダッシュボード画面を表示）
# ========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diet App - 体重管理</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: sans-serif; background-color: #f7f9fc; color: #333; }
        .container { max-width: 600px; margin: 40px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2c3e50; }
        .form-group { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        input { padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
        button { padding: 10px 20px; background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #2ecc71; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📊 体重ダッシュボード</h2>
        <div class="form-group">
            <input type="date" id="dateInput">
            <input type="number" id="weightInput" step="0.1" placeholder="体重 (kg)">
            <button onclick="saveWeight()">登録</button>
        </div>
        <canvas id="weightChart"></canvas>
    </div>
    <script>
        let weightChart;
        async function fetchAndRenderChart() {
            const response = await fetch('/weights/');
            const data = await response.json();
            data.sort((a, b) => new Date(a.date) - new Date(b.date));
            const labels = data.map(item => item.date);
            const weights = data.map(item => item.weight);
            const ctx = document.getElementById('weightChart').getContext('2d');
            if (weightChart) { weightChart.destroy(); }
            
            weightChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '体重 (kg)',
                        data: weights,
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.2)',
                        borderWidth: 2,
                        tension: 0.1
                    }]
                },
                options: { 
                    scales: { 
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day',
                                displayFormats: { day: 'yyyy-MM-dd' }
                            }
                        },
                        y: { beginAtZero: false } 
                    } 
                }
            });
        }
        async function saveWeight() {
            const dateInput = document.getElementById('dateInput').value;
            const weightInput = document.getElementById('weightInput').value;
            if (!dateInput || !weightInput) { alert("日付と体重を両方入力してください！"); return; }
            const response = await fetch('/weights/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: dateInput, weight: parseFloat(weightInput) })
            });
            if (response.ok) { alert("登録しました！グラフを更新します。"); fetchAndRenderChart(); }
        }
        window.onload = fetchAndRenderChart;
    </script>
</body>
</html>
    """

# ========================================
# 1. Weight (体重管理)
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

# ========================================
# 2. Ingredient (食材マスター) ✨復活✨
# ========================================
@app.post("/ingredients/", response_model=schemas.IngredientResponse)
def create_ingredient(ingredient_data: schemas.IngredientCreate, db: Session = Depends(get_db)):
    db_ingredient = models.Ingredient(
        name=ingredient_data.name,
        calories=ingredient_data.calories,
        protein=ingredient_data.protein,
        fat=ingredient_data.fat,
        carbs=ingredient_data.carbs
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).all()

# ========================================
# 3. Recipe (レシピマスター) ✨復活✨
# ========================================
@app.post("/recipes/", response_model=schemas.RecipeResponse)
def create_recipe(recipe_data: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(title=recipe_data.title, instructions=recipe_data.instructions)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(db: Session = Depends(get_db)):
    return db.query(models.Recipe).all()

# ========================================
# 4. MealHistory (食事履歴) ✨復活✨
# ========================================
@app.post("/meal_histories/", response_model=schemas.MealHistoryResponse)
def create_meal_history(meal_data: schemas.MealHistoryCreate, db: Session = Depends(get_db)):
    db_meal = models.MealHistory(
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

@app.get("/meal_histories/", response_model=list[schemas.MealHistoryResponse])
def read_meal_histories(db: Session = Depends(get_db)):
    return db.query(models.MealHistory).all()