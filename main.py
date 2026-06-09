from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import models, schemas
from database import engine, SessionLocal

# データベースにテーブルを自動生成・更新
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
    <title>Diet App - 究極リレーショナル管理</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
    <style>
        body { font-family: sans-serif; background-color: #f7f9fc; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 30px auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #2c3e50; margin-top: 0; }
        .form-group { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
        input, textarea, select { padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; width: 100%; box-sizing: border-box; font-family: sans-serif; }
        textarea { resize: vertical; height: 80px; }
        .inline-inputs { display: flex; gap: 10px; width: 100%; }
        button { padding: 10px 20px; background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; white-space: nowrap; }
        button:hover { background-color: #2ecc71; }
        
        /* レシピ・食材の動的追加用 */
        .ingredient-row { display: flex; gap: 10px; margin-bottom: 10px; align-items: center; }
        .remove-btn { background-color: #c0392b; padding: 10px; }
        .remove-btn:hover { background-color: #e74c3c; }

        /* 本物のレシピカードスタイル */
        .recipe-card { background: #f8f9fa; border-left: 5px solid #9b59b6; padding: 15px; border-radius: 6px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .recipe-title { font-weight: bold; font-size: 18px; color: #8e44ad; margin-bottom: 5px; }
        .recipe-pfc { font-size: 13px; color: #2980b9; background: #eaf2f8; padding: 5px 10px; border-radius: 4px; margin: 5px 0; display: inline-block; }
        .recipe-ingredients-list { font-size: 13px; color: #666; margin-bottom: 10px; padding-left: 20px; }
        .recipe-instructions { font-size: 14px; color: #333; white-space: pre-wrap; border-top: 1px dashed #ddd; padding-top: 8px; }

        /* 提案画面用スタイル */
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
            <input type="text" id="mealNameInput" list="ingredientOptions" placeholder="食べたものを検索... (食材マスターから補完)" oninput="onIngredientSelect()">
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
        <h2>📝 マイレシピ作成 (DB連動型)</h2>
        <div class="form-group" style="flex-direction: column; gap: 10px;">
            <input type="text" id="recipeTitleInput" placeholder="レシピ名 (例: 沼親子丼)">
            
            <div id="recipeIngredientsContainer">
                <label style="font-size: 14px; font-weight: bold; color: #7f8c8d;">🥗 使用する食材と分量</label>
                </div>
            <button type="button" onclick="addIngredientRow()" style="background-color: #34495e; font-size: 14px; padding: 5px 10px; margin-bottom: 10px;">＋ 食材を追加</button>

            <textarea id="recipeInstructionsInput" placeholder="作り方の手順やメモ"></textarea>
            <button onclick="saveRecipe()" style="background-color: #9b59b6; width: 100%;">レシピを保存（自動PFC計算）</button>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <h3>📔 マイレシピ一覧 (基準カロリー自動算出)</h3>
        <div id="recipeList"></div>
    </div>

    <div class="container" style="border: 2px solid #f1c40f;">
        <h2>🔍 食材マスター連動 レシピ提案</h2>
        <div class="form-group">
            <select id="searchIngredientSelect" onchange="searchRecipesByIngredient()">
                <option value="">-- 冷蔵庫にある食材を選択 --</option>
            </select>
        </div>
        <div id="proposalList">
            <p style='color:#888; text-align:center;'>食材を選択すると、中間テーブルを逆引きしておすすめレシピを提案します</p>
        </div>
    </div>

    <script>
        let weightChart;
        let pfcChart;
        let globalIngredients = [];

        const todayStr = new Date().toISOString().split('T')[0];
        document.getElementById('dateInput').value = todayStr;
        document.getElementById('mealDateInput').value = todayStr;

        // --- 体重管理 ---
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
                data: { labels: labels, datasets: [{ label: '体重 (kg)', data: weights, borderColor: '#27ae60', backgroundColor: 'rgba(39, 174, 96, 0.2)', borderWidth: 2, tension: 0.1 }] },
                options: { scales: { x: { type: 'time', time: { unit: 'day', displayFormats: { day: 'yyyy-MM-dd' } } }, y: { beginAtZero: false } } }
            });
        }

        async function saveWeight() {
            const dateInput = document.getElementById('dateInput').value;
            const weightInput = document.getElementById('weightInput').value;
            if (!dateInput || !weightInput) { alert("入力データが足りません"); return; }
            const response = await fetch('/weights/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: dateInput, weight: parseFloat(weightInput) })
            });
            if (response.ok) { alert("登録完了！"); fetchAndRenderWeightChart(); }
        }

        // --- 食材マスターの読み込み（サジェスト＆レシピ紐付け用） ---
        async function loadIngredientsMaster() {
            const response = await fetch('/ingredients/');
            globalIngredients = await response.json();
            
            // 食事入力用のサジェスト設定
            const datalist = document.getElementById('ingredientOptions');
            datalist.innerHTML = "";
            
            // レシピ提案検索用のドロップダウン設定
            const searchSelect = document.getElementById('searchIngredientSelect');
            searchSelect.innerHTML = '<option value="">-- 冷蔵庫にある食材を選択 --</option>';

            globalIngredients.forEach(item => {
                const option = document.createElement('option');
                option.value = item.name;
                datalist.appendChild(option);

                const selectOpt = document.createElement('option');
                selectOpt.value = item.id;
                selectOpt.textContent = `${item.name} (${item.unit || 'g'}ベース)`;
                searchSelect.appendChild(selectOpt);
            });

            // レシピフォームの最初の1行を準備
            if(document.getElementById('recipeIngredientsContainer').children.length <= 1) {
                addIngredientRow();
            }
        }

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

        // --- 食事・PFCダッシュボード ---
        async function fetchAndRenderPfcChart() {
            const selectedDate = document.getElementById('mealDateInput').value;
            if (!selectedDate) return;
            const response = await fetch('/meal_histories/');
            const allMeals = await response.json();
            let totalP = 0, totalF = 0, totalC = 0;
            allMeals.forEach(meal => {
                if (meal.date === selectedDate) {
                    totalP += meal.protein || 0; totalF += meal.fat || 0; totalC += meal.carbs || 0;
                }
            });
            const ctx = document.getElementById('pfcChart').getContext('2d');
            if (pfcChart) { pfcChart.destroy(); }
            if (totalP === 0 && totalF === 0 && totalC === 0) {
                pfcChart = new Chart(ctx, { type: 'doughnut', data: { labels: ['データなし'], datasets: [{ data: [1], backgroundColor: ['#bdc3c7'] }] }, options: { plugins: { title: { display: true, text: '食事データなし' } } } });
                return;
            }
            pfcChart = new Chart(ctx, {
                type: 'doughnut',
                data: { labels: [`P: ${totalP.toFixed(1)}g`, `F: ${totalF.toFixed(1)}g`, `C: ${totalC.toFixed(1)}g`], datasets: [{ data: [totalP, totalF, totalC], backgroundColor: ['#3498db', '#e74c3c', '#f1c40f'] }] },
                options: { plugins: { title: { display: true, text: `${selectedDate} の合計PFC` } } }
            });
        }

        async function saveMeal() {
            const date = document.getElementById('mealDateInput').value;
            const name = document.getElementById('mealNameInput').value;
            const calories = document.getElementById('caloriesInput').value;
            const protein = document.getElementById('proteinInput').value;
            const fat = document.getElementById('fatInput').value;
            const carbs = document.getElementById('carbsInput').value;
            if (!date || !name) { alert("必須項目が空です"); return; }
            const response = await fetch('/meal_histories/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: date, name: name, amount_g: 100, calories: parseFloat(calories) || 0, protein: parseFloat(protein) || 0, fat: parseFloat(fat) || 0, carbs: parseFloat(carbs) || 0 })
            });
            if (response.ok) { alert("食事を記録しました！"); fetchAndRenderPfcChart(); }
        }

        // --- 🥗 レシピ作成画面での食材行の動的追加・削除 ---
        function addIngredientRow() {
            const container = document.getElementById('recipeIngredientsContainer');
            const row = document.createElement('div');
            row.className = 'ingredient-row';
            
            let optionsHtml = globalIngredients.map(item => `<option value="${item.id}">${item.name}</option>`).join('');
            
            row.innerHTML = `
                <select class="row-ingredient-id" style="flex: 2;">
                    ${optionsHtml}
                </select>
                <input type="number" class="row-ingredient-amount" placeholder="分量(gまたは個)" style="flex: 1;" min="1" value="100">
                <button type="button" class="remove-btn" onclick="this.parentElement.remove()">✕</button>
            `;
            container.appendChild(row);
        }

        // --- 本物のレシピ保存（中間テーブルデータを添えて） ---
        async function saveRecipe() {
            const title = document.getElementById('recipeTitleInput').value;
            const instructions = document.getElementById('recipeInstructionsInput').value;
            if (!title) { alert("レシピ名を入力してください"); return; }

            // 画面上の食材入力行から、IDと分量をすべて回収する
            const ingredientRows = document.querySelectorAll('.ingredient-row');
            const ingredientsData = [];
            ingredientRows.forEach(row => {
                const ingredientId = row.querySelector('.row-ingredient-id').value;
                const amount = row.querySelector('.row-ingredient-amount').value;
                if(ingredientId && amount) {
                    ingredientsData.push({
                        ingredient_id: parseInt(ingredientId),
                        amount: parseFloat(amount)
                    });
                }
            });

            const response = await fetch('/recipes/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    instructions: instructions,
                    ingredients: ingredientsData
                })
            });

            if (response.ok) {
                alert("食材と紐づいた本格レシピを登録しました！");
                document.getElementById('recipeTitleInput').value = "";
                document.getElementById('recipeInstructionsInput').value = "";
                // 食材入力行をリセット
                document.getElementById('recipeIngredientsContainer').innerHTML = '<label style="font-size: 14px; font-weight: bold; color: #7f8c8d;">🥗 使用する食材と分量</label>';
                addIngredientRow();
                fetchAndRenderRecipes();
            }
        }

        // --- 📖 レシピ一覧の描画（裏側で計算された総PFCを出力） ---
        async function fetchAndRenderRecipes() {
            const response = await fetch('/recipes/');
            const recipes = await response.json();
            const recipeList = document.getElementById('recipeList');
            recipeList.innerHTML = "";

            if (recipes.length === 0) {
                recipeList.innerHTML = "<p style='color:#888; text-align:center;'>登録されたレシピはありません</p>";
                return;
            }

            recipes.forEach(recipe => {
                // 中間テーブルから紐づいた食材のテキストを作成
                let ingTxt = recipe.ingredients.map(ri => `<li>${ri.ingredient.name}: ${ri.amount}${ri.ingredient.unit || 'g'}</li>`).join('');
                
                const card = document.createElement('div');
                card.className = 'recipe-card';
                card.innerHTML = `
                    <div class="recipe-title">🍳 ${recipe.title}</div>
                    <div class="recipe-pfc">
                        🔥 総計: ${recipe.total_calories.toFixed(1)} kcal | 
                        P: ${recipe.total_protein.toFixed(1)}g | 
                        F: ${recipe.total_fat.toFixed(1)}g | 
                        C: ${recipe.total_carbs.toFixed(1)}g
                    </div>
                    <ul class="recipe-ingredients-list">
                        ${ingTxt || '<li>紐付けられた食材はありません</li>'}
                    </ul>
                    <div class="recipe-instructions">${recipe.instructions || '手順なし'}</div>
                `;
                recipeList.appendChild(card);
            });
        }

        // --- 🕵️‍♂️ 【新・提案魔法】食材マスターのIDから中間テーブルを正確に逆引き検索 ---
        async function searchRecipesByIngredient() {
            const selectedIngredientId = document.getElementById('searchIngredientSelect').value;
            const proposalList = document.getElementById('proposalList');

            if (!selectedIngredientId) {
                proposalList.innerHTML = "<p style='color:#888; text-align:center;'>食材を選択すると、中間テーブルを逆引きしておすすめレシピを提案します</p>";
                return;
            }

            const response = await fetch('/recipes/');
            const recipes = await response.json();

            // 中間テーブルの配列（ingredients）の中に、選んだ食材IDが含まれるレシピを厳密に抽出！
            const matchedRecipes = recipes.filter(recipe => {
                return recipe.ingredients.some(ri => ri.ingredient_id == selectedIngredientId);
            });

            proposalList.innerHTML = "";

            if (matchedRecipes.length === 0) {
                proposalList.innerHTML = `<p style='color:#e74c3c; text-align:center;'>この食材を使用するレシピはまだDBに登録されていません</p>`;
                return;
            }

            matchedRecipes.forEach(recipe => {
                const card = document.createElement('div');
                card.className = 'proposal-card';
                card.innerHTML = `
                    <div class="proposal-title">💡 おすすめ：${recipe.title}</div>
                    <div style="font-size: 13px; color: #d35400; margin-bottom: 5px; font-weight: bold;">
                        🔥 この1食の基準値: ${recipe.total_calories.toFixed(1)} kcal (P:${recipe.total_protein.toFixed(1)}g F:${recipe.total_fat.toFixed(1)}g C:${recipe.total_carbs.toFixed(1)}g)
                    </div>
                    <div class="recipe-instructions" style="color: #666;">${recipe.instructions}</div>
                `;
                proposalList.appendChild(card);
            });
        }

        // --- 🚀 起動 ---
        window.onload = async function() {
            fetchAndRenderWeightChart();
            fetchAndRenderPfcChart();
            await loadIngredientsMaster();
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
        carbs=ingredient_data.carbs,
        unit=ingredient_data.unit
    )
    db.add(db_ingredient)
    db.commit()
    db.refresh(db_ingredient)
    return db_ingredient

@app.get("/ingredients/", response_model=list[schemas.IngredientResponse])
def read_ingredients(db: Session = Depends(get_db)):
    return db.query(models.Ingredient).all()

# ========================================
# 3. Recipe (レシピマスター：✨リレーショナル自動計算版)
# ========================================
@app.post("/recipes/", response_model=schemas.RecipeResponse)
def create_recipe(recipe_data: schemas.RecipeCreate, db: Session = Depends(get_db)):
    db_recipe = models.Recipe(title=recipe_data.title, instructions=recipe_data.instructions)
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)

    for ing_part in recipe_data.ingredients:
        db_ri = models.RecipeIngredient(
            recipe_id=db_recipe.id,
            ingredient_id=ing_part.ingredient_id,
            amount=ing_part.amount
        )
        db.add(db_ri)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe

@app.get("/recipes/", response_model=list[schemas.RecipeResponse])
def read_recipes(db: Session = Depends(get_db)):
    # ✨修正：models.pyの自動計算プロパティのおかげで、ここの手動計算ループが不要になりました！超スッキリ！
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

# ✨修正：全件取得によるフリーズを防ぐため、日付（date）で絞り込めるように改良！
@app.get("/meal_histories/", response_model=list[schemas.MealHistoryResponse])
def read_meal_histories(date: Optional[date] = None, db: Session = Depends(get_db)):
    query = db.query(models.MealHistory)
    if date:
        query = query.filter(models.MealHistory.date == date)
    return query.all()

# --- 🧹 食事履歴の削除API ---
@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    db_meal = db.query(models.MealHistory).filter(models.MealHistory.id == meal_id).first()
    if not db_meal:
        # ✨修正：エラー時は200ではなく、正しいHTTPステータスコード（404）を返す！
        raise HTTPException(status_code=404, detail="Meal not found")
    
    db.delete(db_meal)
    db.commit()
    return {"status": "success", "message": f"Meal {meal_id} deleted"}