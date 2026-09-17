from flask import Flask, render_template, request
import pickle
import pandas as pd

app = Flask(__name__)

# Load the trained pipeline
try:
    with open('pipe.pkl', 'rb') as file:
        model = pickle.load(file)
    print("✅ Model loaded successfully!")
except FileNotFoundError:
    print("❌ Error: 'pipe.pkl' file not found in the current directory!")
    model = None


# ── Dashboard (home page) ──
@app.route('/')
def dashboard():
    return render_template('dashboard.html')


# ── Predict Page (GET) + Prediction (POST) ──
@app.route('/predict', methods=['GET', 'POST'])  # ✅ added GET
def predict():
    if request.method == 'GET':
        return render_template('index.html')      # ✅ just show the form

    if model is None:
        return render_template('index.html', error="Model not loaded. Please check if 'pipe.pkl' exists.")

    try:
        data = {
            'age': float(request.form['age']),
            'heart_rate': float(request.form['heart_rate']),
            'systolic_blood_pressure': float(request.form['systolic_blood_pressure']),
            'oxygen_saturation': float(request.form['oxygen_saturation']),
            'body_temperature': float(request.form['body_temperature']),
            'pain_level': int(request.form['pain_level']),
            'chronic_disease_count': int(request.form['chronic_disease_count']),
            'previous_er_visits': int(request.form['previous_er_visits']),
            'arrival_mode': request.form['arrival_mode']
        }

        input_df = pd.DataFrame([data])

        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df).max() * 100

        triage_levels = {
            0: "Level 0 - Non-Urgent",
            1: "Level 1 - Less Urgent",
            2: "Level 2 - Urgent",
            3: "Level 3 - Emergent / Life-threatening"
        }

        result = triage_levels.get(prediction, "Unknown")

        return render_template('index.html',
                               prediction_text=result,
                               probability=round(probability, 2),
                               input_data=data)

    except Exception as e:
        return render_template('index.html', error=f"Prediction error: {str(e)}")


# ── Local Development ──
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)