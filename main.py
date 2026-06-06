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
# 🏠 案内係（すべての画面が1つに融合した神の領域）
# ========================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Diet App - 究極統合管理</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: sans-serif; background-color: #f7f9fc; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 30px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2c3e50; margin-top: 0; }
        .form-group { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        input, textarea { padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; width: 100%; box-sizing: border-box; font-family: sans-serif; }
        textarea { resize: vertical; height: 80px; }
        .inline-inputs { display: flex; gap: 10px; width: 100%; }
        button { padding: 10px 20px; background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; white-space: nowrap; }
        button:hover { background-color: #2ecc71; }
        
        /* レシピ用のスタイル */
        .recipe-card { background: #f8f9fa; border-left: 5px solid #9b59b6; padding: 15px; border-radius: 6px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .recipe-title { font-weight: bold; font-size: 18px; color: #8e44ad; margin-bottom: 5px; }
        .recipe-instructions { font-size: 14px; color: #555; white-space: pre-wrap; }

        /* 提案画面用の新スタイル（プレミアムゴールド） */
        .proposal-card { background: #fffdf0; border: 1px solid #f1c40f; border-left: 5px solid #f1c40f; padding: 15px; border-radius: 6px; margin-bottom: 15px; }
        .proposal-title { font-weight: bold; font-size: 18px; color: #d35400; margin-bottom: 5px; }
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
            
            <input type="text" id="mealNameInput" list="ingredientOptions" placeholder="食べたもの、または食材を検索... (例: 鶏胸肉)" oninput="onIngredientSelect()">
            <datalist id="ingredientOptions"></datalist>

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

    <div class="container">
        <h2>📝 マイレシピ作成</h2>
        <div class="form-group" style="flex-direction: column; gap: 10px;">
            <input type="text" id="recipeTitleInput" placeholder="レシピ名 (例: PFC最強親子丼)">
            <textarea id="recipeInstructionsInput" placeholder="作り方やメモ (例: 鶏胸肉200g、卵2個、玉ねぎ半分をめんつゆで煮る)"></textarea>
            <button onclick="saveRecipe()" style="background-color: #9b59b6; width: 100%;">レシピを保存</button>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3>📔 マイレシピ一覧</h3>
        <div id="recipeList"></div>
    </div>

    <div class="container" style="border: 2px solid #f1c40f;">
        <h2>🔍 手元にある食材からレシピ提案</h2>
        <div class="form-group">
            <input type="text" id="searchKeywordInput" placeholder="冷蔵庫にある食材を入力... (例: 鶏胸肉)" oninput="searchRecipes()">
        </div>
        <div id="proposalList">
            <p style='color:#888; text-align:center;'>食材を入力すると、おすすめレシピが自動提案されます</p>
        </div>
    </div>

    <script>
        let weightChart;
        let pfcChart;
        let globalIngredients = [];

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

        // --- 🔍 食材マスター候補読み込み ---
        async function loadIngredientsMaster() {
            const response = await fetch('/ingredients/');
            globalIngredients = await response.json();
            const datalist = document.getElementById('ingredientOptions');
            datalist.innerHTML = "";
            globalIngredients.forEach(item => {
                const option = document.createElement('option');
                option.value = item.name;
                datalist.appendChild(option);
            });
        }

        // --- ⚡️ 食材チャージ機能 ---
        function onIngredientSelect() {
            const currentInput = document.getElementById('mealNameInput').value;
            const matchedIngredient = globalIngredients.find(item => item.name === currentInput);
            if (matchedIngredient) {
                document.getElementById('caloriesInput').value = matchedIngredient.calories;
                document.getElementById('proteinInput').value = matchedIngredient.protein;
                document.getElementById('fatInput').value = matchedIngredient.fat;
                document.getElementById('carbsInput').value = matchedIngredient.carbs;
            }
        }

        // --- 🍩 PFC円グラフを描く魔法 ---
        async function fetchAndRenderPfcChart() {
            const selectedDate = document.getElementById('mealDateInput').value;
            if (!selectedDate) return;

            const response = await fetch('/meal_histories/');
            const allMeals = await response.json();

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

            if (totalP === 0 && totalF === 0 && totalC === 0) {
                pfcChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: { labels: ['データなし'], datasets: [{ data: [1], backgroundColor: ['#bdc3c7'] }] },
                    options: { plugins: { title: { display: true, text: 'この日の食事データはありません' } } }
                });
                return;
            }

            pfcChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: [`タンパク質 (P): ${totalP}g`, `脂質 (F): ${totalF}g`, `炭水化物 (C): ${totalC}g`],
                    datasets: [{ data: [totalP, totalF, totalC], backgroundColor: ['#3498db', '#e74c3c', '#f1c40f'] }]
                },
                options: { plugins: { title: { display: true, text: `${selectedDate} のPFCバランス` } } }
            });
        }

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
                    date: date, name: name, amount_g: 100,
                    calories: parseFloat(calories) || 0, protein: parseFloat(protein) || 0, fat: parseFloat(fat) || 0, carbs: parseFloat(carbs) || 0
                })
            });

            if (response.ok) {
                alert("食事を記録しました！");
                document.getElementById('mealNameInput').value = "";
                document.getElementById('caloriesInput').value = "";
                document.getElementById('proteinInput').value = "";
                document.getElementById('fatInput').value = "";
                document.getElementById('carbsInput').value = "";
                fetchAndRenderPfcChart();
            }
        }

        // --- 📖 レシピ一覧を描く魔法 ---
        async function fetchAndRenderRecipes() {
            const response = await fetch('/recipes/');
            const recipes = await response.json();
            const recipeList = document.getElementById('recipeList');
            recipeList.innerHTML = "";

            if (recipes.length === 0) {
                recipeList.innerHTML = "<p style='color:#888; text-align:center;'>登録されたレシピはまだありません</p>";
                return;
            }

            recipes.forEach(recipe => {
                const card = document.createElement('div');
                card.className = 'recipe-card';
                card.innerHTML = `
                    <div class="recipe-title">🍳 ${recipe.title}</div>
                    <div class="recipe-instructions">${recipe.instructions || '作り方の登録はありません'}</div>
                `;
                recipeList.appendChild(card);
            });
        }

        async function saveRecipe() {
            const title = document.getElementById('recipeTitleInput').value;
            const instructions = document.getElementById('recipeInstructionsInput').value;
            if (!title) { alert("レシピ名は必ず入力してください！"); return; }

            const response = await fetch('/recipes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title, instructions: instructions })
            });

            if (response.ok) {
                alert("マイレシピを登録しました！");
                document.getElementById('recipeTitleInput').value = "";
                document.getElementById('recipeInstructionsInput').value = "";
                fetchAndRenderRecipes();
            }
        }

        // --- 🕵️‍♂️ 食材からレシピをリアルタイム大検索する究極の魔法 ---
        async function searchRecipes() {
            const keyword = document.getElementById('searchKeywordInput').value.trim();
            const proposalList = document.getElementById('proposalList');

            if (!keyword) {
                proposalList.innerHTML = "<p style='color:#888; text-align:center;'>食材を入力すると、おすすめレシピが自動提案されます</p>";
                return;
            }

            const response = await fetch('/recipes/');
            const recipes = await response.json();

            const matchedRecipes = recipes.filter(recipe => {
                return recipe.instructions && recipe.instructions.includes(keyword);
            });

            proposalList.innerHTML = "";

            if (matchedRecipes.length === 0) {
                proposalList.innerHTML = `<p style='color:#e74c3c; text-align:center;'>「${keyword}」を使うレシピはまだ登録されていません</p>`;
                return;
            }

            matchedRecipes.forEach(recipe => {
                const card = document.createElement('div');
                card.className = 'proposal-card';
                card.innerHTML = `
                    <div class="proposal-title">💡 おすすめ：${recipe.title}</div>
                    <div class="recipe-instructions" style="color: #666;">${recipe.instructions}</div>
                `;
                proposalList.appendChild(card);
            });
        }

        // --- 🚀 画面が開いた瞬間にすべてを起動 ---
        window.onload = function() {
            fetchAndRenderWeightChart();
            fetchAndRenderPfcChart();
            loadIngredientsMaster();
            fetchAndRenderRecipes();
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