import requests
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)

#app.secret_key = "your-secret-key"
mongo_uri = "mongodb+srv://User:.@mealprepper.4ko8v.mongodb.net/?retryWrites=true&w=majority&appName=MealPrepper"
client = MongoClient(mongo_uri)
db = client.meal_prepper
meal_plans = db.meal_plans
users = db.users

headers = {
    "x-rapidapi-key": "6849c0c816mshb4e9ebc6fe79ea9p17c2e7jsn8c871f624f35",
    "x-rapidapi-host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"
}
DaysInAWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def is_logged_in():
    return 'username' in session
@app.route('/register', methods=['GET', 'POST'])
def register():
    data = request.json
    if request.method == 'POST':
        username = data.get('username')
        password = data.get('password')

        if users.find_one({"username": username}):
            flash("Username already exists", "error")
            #return redirect(url_for('register'))


        users.insert_one({"username": username, "password": password})
        flash("Registration successful! Please log in.", "success")
        #return redirect(url_for('login'))
        return jsonify({"message": "User registered successfully"})
@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.json
    if request.method == 'POST':
        username = data.get('username')
        password = data.get('password')

        # Find user in database
        user = users.find_one({"username": username})

        if user and password == user['password']:
            session['username'] = username

            return jsonify({"message": "Login successful!", "status": "success"})   #Do not have a dashboard yet
        else:

            return jsonify({"message": "Invalid username or password", "status": "error"})

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

def get_ServingID(maxCalories,minCalories,FilterItems):
    querystring = {
        "random": "true",
        "number": "1",
        "maxCalories": maxCalories,
        "minCalories": minCalories,
    }
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/findByNutrients"
    response = requests.get(url, headers=headers, params=(querystring|FilterItems)).json()
    return response

def get_PlateInfo(ID):
    url = f"https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{ID}/information"
    Info = requests.get(url, headers=headers).json()

    url = f"https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{ID}/ingredientWidget.json"
    Ingredients = requests.get(url, headers=headers).json()
    
    url = f"https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{ID}/nutritionWidget.json"
    Nutrition = requests.get(url, headers=headers).json()
    
    response = {
        "Information": Info,
        "Ingredients": Ingredients,
        "Nutrition": Nutrition,
    }

    return response

def set_Day(ServingsPerDay,DailyCaloricIntake,FilterItems):
    maxCalories = int(DailyCaloricIntake)
    totalCalories = 0
    Day = {}
    for num in range(int(ServingsPerDay)):
        ServingID = num + 1
        minCalories = maxCalories/2
        Plate = get_ServingID(maxCalories, minCalories, FilterItems)

        PlateCalories = int(Plate[0]["calories"])
        maxCalories = maxCalories - PlateCalories
        totalCalories = totalCalories + PlateCalories
        
        PlateID = Plate[0]["id"]
        PlateInfo = get_PlateInfo(PlateID)
        temp = {f"Serving {str(ServingID)}":PlateInfo,}

        Day = Day|temp
    
    return Day|{"totalCaloriesPerDiem":totalCalories}

def set_Week(ServingsPerDay,DailyCaloricIntake,FilterItems):
    Week = {}
    for Day in DaysInAWeek:
        TempDay = set_Day(ServingsPerDay,DailyCaloricIntake,FilterItems)
        temp = { Day: TempDay}
        Week = Week|temp
    
    return Week

def save_meal_plan(plan_type, plan_data):
    document = {
        "type": plan_type,
        "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "plan": plan_data
    }
    result = meal_plans.insert_one(document)
    if is_logged_in():
        users.update_one(
            {"username": session['username']},
            {"$push": {"recent_meal_plan_ids": result.inserted_id}}
        )
    return str(result.inserted_id)

def get_meal_plan(plan_id):
    plan = meal_plans.find_one({"_id": ObjectId(plan_id)})
    if plan:
        plan['_id'] = str(plan['_id'])  # Convert ObjectId to string
    return plan

@app.route('/Generate_Day', methods=['GET'])
def get_GenDay():
    DailyCaloricIntake = str(request.args.get('DailyCaloricIntake'))
    ServingsPerDay = str(request.args.get('ServingsPerDay'))
    excludeIngredients = str(request.args.get('excludeIngredients'))
    intolerances = str(request.args.get('intolerances'))
    diet = str(request.args.get('diet'))

    FilterItems = {
        "diet": diet,
        "excludeIngredients": excludeIngredients,
        "intolerances": intolerances,
    }

    Day = set_Day(ServingsPerDay, DailyCaloricIntake, FilterItems)
    
    plan_id = save_meal_plan("day", Day)
    
    return {"plan_id": plan_id, "meal_plan": Day}

@app.route('/Generate_Week', methods=['GET'])
def get_GenWeek():
    DailyCaloricIntake = str(request.args.get('DailyCaloricIntake'))
    ServingsPerDay = str(request.args.get('ServingsPerDay'))
    excludeIngredients = str(request.args.get('excludeIngredients'))
    intolerances = str(request.args.get('intolerances'))
    diet = str(request.args.get('diet'))

    FilterItems = {
        "diet": diet,
        "excludeIngredients": excludeIngredients,
        "intolerances": intolerances,
    }

    Week = set_Week(ServingsPerDay, DailyCaloricIntake, FilterItems)
    
    plan_id = save_meal_plan("week", Week)
    
    return {"plan_id": plan_id, "meal_plan": Week}

@app.route('/Get_Meal_Plan/<plan_id>', methods=['GET'])
def retrieve_meal_plan(plan_id):
    plan = get_meal_plan(plan_id)
    if plan:
        return plan
    else:
        return {"error": "Meal plan not found"}, 404



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)