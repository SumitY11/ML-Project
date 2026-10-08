# 🌾 AgriSmart - Crop Yield & AI Climate Risk Intelligence Platform

AgriSmart is an end-to-end Machine Learning powered agricultural intelligence platform designed to forecast crop yields, assess climate anomaly risks, recommend optimal regional crops, analyze historical agricultural trends, and simulate what-if agronomic management scenarios.

---

## ✨ Key Features

- **🌱 ML Crop Yield Predictor:** Real-time crop yield forecasting (Tonnes/Hectare) and total harvest estimation based on land area, sowing season, expected monsoonal rainfall, fertilizer/pesticide input levels, and historical temperature records.
- **🤖 AI Optimal Crop Recommender Engine:** Intelligent crop recommendation pipeline that evaluates all supported crop varieties for a given region and season, ranking the **Top 5 Highest Yielding & Most Lucrative Crops** with podium rank cards (🥇 Gold, 🥈 Silver, 🥉 Bronze).
- **📊 Crop Suitability & Financial Revenue Estimator:** Calculates an AI Crop Match Suitability Index (%) comparing predicted yields to regional benchmarks, alongside estimated market harvest value (in ₹ Lakhs).
- **📈 Historical Analytics Dashboard:** Interactive trend visualizers for 20+ years of crop yields and monsoonal precipitation, peak/lowest yield KPIs, and top producing state leaderboards.
- **⚖️ What-If Scenario Comparator:** Side-by-side strategy simulator allowing farmers and agronomists to evaluate yield variance and percentage gains between baseline vs. optimized input strategies.
- **💡 Agronomic Advisory & Best Practices Guide:** Tailored mitigation strategies covering Soil & Nutrient Optimization (NPK), Climate Water Resilience, Integrated Pest Management (IPM), and Crop Rotation.
- **📡 REST API & Web Application:** High-performance FastAPI REST API endpoints served alongside a custom glassmorphic web application (`web_app/`).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Machine Learning** | Scikit-Learn (RandomForestRegressor, GradientBoosting, ColumnTransformer, OneHotEncoder), Joblib, NumPy, Pandas |
| **Backend API** | FastAPI, Uvicorn, Pydantic, CORS Middleware |
| **Dashboards & UI** | Streamlit (Custom Cyber-Emerald Glassmorphism CSS), HTML5, Vanilla CSS3, JavaScript (ES6+), Chart.js |
| **Data Sources** | 19,689 Crop Yield Records (1997-2020), 117-Year Temperature Records (1901-2017) |

---

## 📁 Project Structure

```text
smart-crop-yield-prediction/
│
├── app.py                   # Main Streamlit Cyber-Emerald UI Dashboard
├── api.py                   # FastAPI REST API Backend & Endpoint handlers
├── run_server.py            # Launcher script for Uvicorn REST API server
├── requirements.txt         # Project dependencies list
├── README.md                # Project documentation
│
├── data/                    # Dataset directory
│   ├── crop_yield.csv       # 19,689 agricultural records across 27 crops & 33 states
│   └── temperatures.csv     # 117-year historical seasonal temperature records
│
├── model/                   # Serialized ML assets
│   ├── crop_yield_model.pkl # Trained Machine Learning Pipeline model
│   └── risk_thresholds.pkl  # Calibrated weather risk quantile thresholds
│
├── notebooks/               # Data Science & Model Training
│   └── Smart_Crop_Yield_Prediction.ipynb # Model training & EDA notebook
│
├── web_app/                 # Standalone Custom Web Application
│   ├── index.html           # Web app structure
│   ├── styles.css           # Glassmorphism dark theme styling
│   └── app.js               # Frontend API integration & Chart.js controllers
│
└── scratch/                 # Utility & test scripts
    └── test_load_model.py   # Standalone model verification script
```

---

## 🚀 Quick Start & Installation

### Step 1: Clone or Open Project Directory
```bash
cd "d:\B.Tech\Sem 5\ML\ML Project\smart-crop-yield-prediction"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🖥️ Running the Application

You can launch AgriSmart using **two different interfaces**:

### Option 1: Streamlit Interactive Dashboard (Recommended)
Launches the full multi-tab Streamlit web application with dynamic sliders, AI Recommender, and glassmorphic UI cards:

```bash
streamlit run app.py
```
👉 Access in browser: **`http://localhost:8501`**

---

### Option 2: FastAPI REST API & Custom Web App
Launches the Uvicorn REST API backend server along with the custom web frontend:

```bash
python run_server.py
```
👉 Access Web Application: **`http://localhost:8000`**  
👉 Access Interactive API Documentation (Swagger): **`http://localhost:8000/docs`**

---

## 📡 REST API Endpoints Overview

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/options` | `GET` | Returns lists of available crops, states, seasons, and years |
| `/api/predict` | `POST` | Accepts farm parameters & returns predicted yield, total tonnage, climate risk status & advisory |
| `/api/recommend` | `GET` | Evaluates all crops and returns top 5 AI recommended crops for a region & season |
| `/api/analytics` | `GET` | Returns historical yield trend lines, rainfall trends, and top state leaderboards |
| `/docs` | `GET` | Interactive Swagger OpenAPI documentation and testing playground |

---

## ⚙️ Virtual Environment (`.venv`) Guidance

If you notice a `.venv` directory located outside the project folder at `d:\B.Tech\Sem 5\ML\ML Project\.venv`:

- **What is `.venv`?**  
  `.venv` is a Python Virtual Environment folder generated by VS Code, PyCharm, or Python's `venv` module. It contains an isolated Python binary and installed `site-packages` for your ML workspace.

- **Should you delete it or not?**
  - **Do NOT delete it if you are using it!** If your VS Code / IDE terminal prompt displays `(.venv)` at the beginning of the command line, it means your active terminal session is using that environment to run `streamlit` and `python`.
  - **When is it safe to delete?** If you plan to create a fresh virtual environment inside your project folder (e.g. `python -m venv venv`), you can safely delete the external `.venv` folder to free up disk space.

---

## 📜 License & Credits

Developed as an advanced Machine Learning & Agronomic Intelligence project. Data sourced from Ministry of Agriculture & Farmers Welfare datasets and Indian Meteorological Department climate records.
