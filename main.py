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
# 🏠 案内係（体重＆食事・PFCグラフの完全版）
# ========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diet App - 統合管理</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: sans-serif; background-color: #f7f9fc; color: #333; }
        .container { max-width: 600px; margin: 40px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2c3e50; }
        .form-group { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        input { padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; width: 100%; box-sizing: border-box; }
        .inline-inputs { display: flex; gap: 10px; width: 100%; }
        button { padding: 10px 20px; background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; white-space: nowrap; }
        button:hover { background-color: #2ecc71; }
    </style>
</head>
<body>

    <div class="container">
        <h2>📊 体重ダッシュボード</h2>
        <div class="form-group">
            <input type="date" id="dateInput" style="max-width: 150px;">
            <input type="number" id="weightInput" step="0.1" placeholder="体重 (kg)">
            <button onclick="saveWeight()">登録</button>
        </div>
        <canvas id="weightChart"></canvas>
    </div>

    <div class="container">
        <h2>🍳 食事・PFCダッシュボード</h2>
        <div class="form-group" style="flex-direction: column; gap: 10px;">
            <input type="date" id="mealDateInput" onchange="fetchAndRenderPfcChart()">
            <input type="text" id="mealNameInput" placeholder="食べたものの名前 (例: 鶏胸肉炒め)">
            <div class="inline-inputs">
                <input type="number" id="caloriesInput" placeholder="カロリー (kcal)">
                <input type="number" id="proteinInput" placeholder="P (g)">
                <input type="number" id="fatInput" placeholder="F (g)">
                <input type="number" id="carbsInput" placeholder="C (g)">
            </div>
            <button onclick="saveMeal()" style="background-color: #e67e22; width: 100%;">食事を記録</button>
        </div>
        
        <div style="max-width: 300px; margin: 0 auto;">
            <canvas id="pfcChart"></canvas>
        </div>
    </div>

    <script>
        let weightChart;
        let pfcChart;

        // 今日の日付をカレンダーの初期値としてセットする
        const todayStr = new Date().toISOString().split('T')[0];
        document.getElementById('dateInput').value = todayStr;
        document.getElementById('mealDateInput').value = todayStr;

        // --- 🏃‍♂️ 体重グラフを描く魔法 ---
        async function fetchAndRenderWeightChart() {
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
                options: { scales: { x: { type: 'time', time: { unit: 'day', displayFormats: { day: 'yyyy-MM-dd' } } }, y: { beginAtZero: false } } }
            });
        }

        // --- 📥 体重を裏側にセーブする魔法 ---
        async function saveWeight() {
            const dateInput = document.getElementById('dateInput').value;
            const weightInput = document.getElementById('weightInput').value;
            if (!dateInput || !weightInput) { alert("日付と体重を両方入力してください！"); return; }
            const response = await fetch('/weights/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: dateInput, weight: parseFloat(weightInput) })
            });
            if (response.ok) { alert("体重を登録しました！"); fetchAndRenderWeightChart(); }
        }

        // --- 🍩 選択された日付の食事データを集計して、PFC円グラフを描く魔法 ---
        async function fetchAndRenderPfcChart() {
            const selectedDate = document.getElementById('mealDateInput').value;
            if (!selectedDate) return;

            // 全ての食事履歴を裏側から取ってくる
            const response = await fetch('/meal_histories/');
            const allMeals = await response.json();

            // 選択された日付のデータだけに絞り込んで、P・F・Cの合計を計算する
            let totalP = 0, totalF = 0, totalC = 0;
            allMeals.forEach(meal => {
                if (meal.date === selectedDate) {
                    totalP += meal.protein || 0;
                    totalF += meal.fat || 0;
                    totalC += meal.carbs || 0;
                }
            });

            const ctx = document.getElementById('pfcChart').getContext('2d');
            if (pfcChart) { pfcChart.destroy(); }

            // もしその日に何も食べていなければ、空っぽ用のグレーの円を出す
            if (totalP === 0 && totalF === 0 && totalC === 0) {
                pfcChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['データなし'],
                        datasets: [{ data: [1], backgroundColor: ['#bdc3c7'] }]
                    },
                    options: { plugins: { title: { display: true, text: 'この日の食事データはありません' } } }
                });
                return;
            }

            // データがあれば、綺麗なPFCドーナツグラフを描く！
            pfcChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [`タンパク質 (P): ${totalP}g`, `脂質 (F): ${totalF}g`, `炭水化物 (C): ${totalC}g`],
                    datasets: [{
                        data: [totalP, totalF, totalC],
                        backgroundColor: ['#3498db', '#e74c3c', '#f1c40f'] // 青(P)、赤(F)、黄(C)
                    }]
                },
                options: { plugins: { title: { display: true, text: `${selectedDate} のPFCバランス` } } }
            });
        }

        // --- 📥 食事データを裏側にセーブする魔法 ---
        async function saveMeal() {
            const date = document.getElementById('mealDateInput').value;
            const name = document.getElementById('mealNameInput').value;
            const calories = document.getElementById('caloriesInput').value;
            const protein = document.getElementById('proteinInput').value;
            const fat = document.getElementById('fatInput').value;
            const carbs = document.getElementById('carbsInput').value;

            if (!date || !name) { alert("日付と食事名は必ず入力してください！"); return; }

            const response = await fetch('/meal_histories/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: date,
                    name: name,
                    amount_g: 100, // 簡易的に100g固定
                    calories: parseFloat(calories) || 0,
                    protein: parseFloat(protein) || 0,
                    fat: parseFloat(fat) || 0,
                    carbs: parseFloat(carbs) || 0
                })
            });

            if (response.ok) {
                alert("食事を記録しました！");
                // 入力欄を綺麗に空っぽにする
                document.getElementById('mealNameInput').value = "";
                document.getElementById('caloriesInput').value = "";
                document.getElementById('proteinInput').value = "";
                document.getElementById('fatInput').value = "";
                document.getElementById('carbsInput').value = "";
                // グラフを最新に更新
                fetchAndRenderPfcChart();
            } else {
                alert("食事の記録に失敗しました。");
            }
        }

        // --- 🚀 画面が開いた瞬間に、体重グラフとPFCグラフを両方自動で描く ---
        window.onload = function() {
            fetchAndRenderWeightChart();
            fetchAndRenderPfcChart();
        };
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
# 2. Ingredient (食材マスター)
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
# 3. Recipe (レシピマスター)
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
# 4. MealHistory (食事履歴)
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