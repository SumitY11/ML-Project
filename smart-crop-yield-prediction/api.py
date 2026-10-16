from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
import time
from datetime import datetime

app = FastAPI(title="Smart Crop Yield Prediction API", version="1.0.0")

# -----------------------------
# Real-Time Inference Monitoring State
# -----------------------------
inference_stats = {
    "count": 0,
    "total_latency_ms": 0.0,
    "last_latency_ms": 0.0,
    "last_timestamp": None,
    "last_crop": None,
    "last_yield": 0.0
}

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global Data & Model Setup
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model", "crop_yield_model.pkl")
RISK_PATH = os.path.join(BASE_DIR, "model", "risk_thresholds.pkl")
CROP_DATA_PATH = os.path.join(BASE_DIR, "data", "crop_yield.csv")
TEMP_DATA_PATH = os.path.join(BASE_DIR, "data", "temperatures.csv")

try:
    crop_df = pd.read_csv(CROP_DATA_PATH)
    for col in ["Crop", "State", "Season"]:
        if col in crop_df.columns:
            crop_df[col] = crop_df[col].astype(str).str.strip()
except Exception as e:
    crop_df = pd.DataFrame()

try:
    temp_df = pd.read_csv(TEMP_DATA_PATH)
except Exception as e:
    temp_df = pd.DataFrame()

try:
    risk_values = joblib.load(RISK_PATH)
except Exception as e:
    risk_values = {
        "rainfall_low": 500, "rainfall_high": 2500,
        "temperature_low": 18, "temperature_high": 35
    }

def get_or_train_model():
    if os.path.exists(MODEL_PATH):
        try:
            m = joblib.load(MODEL_PATH)
            test_df = pd.DataFrame({
                "Crop": ["Rice"], "Crop_Year": [2017], "Season": ["Kharif"],
                "State": ["Assam"], "Area": [2.5], "Annual_Rainfall": [1400.0],
                "Fertilizer": [2500000.0], "Pesticide": [10000.0], "Season_Temperature": [26.5]
            })
            _ = m.predict(test_df)
            print("Loaded existing ML model successfully.")
            return m
        except Exception as e:
            print(f"Existing model incompatible with current environment ({e}). Training native model...")

    if crop_df.empty:
        return None

    try:
        from sklearn.compose import ColumnTransformer
        from sklearn.preprocessing import OneHotEncoder
        from sklearn.pipeline import Pipeline
        from sklearn.ensemble import RandomForestRegressor

        features = ["Crop", "Crop_Year", "Season", "State", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide", "Season_Temperature"]
        df = crop_df.copy()
        if "Season_Temperature" not in df.columns:
            df["Season_Temperature"] = 26.5

        X = df[features]
        y = df["Yield"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Crop", "Season", "State"]),
                ("num", "passthrough", [c for c in features if c not in ["Crop", "Season", "State"]])
            ]
        )

        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1))
        ])

        pipeline.fit(X, y)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(pipeline, MODEL_PATH)
        print(f"Native ML model trained and saved to {MODEL_PATH}!")
        return pipeline
    except Exception as ex:
        print("Failed to train model:", ex)
        return None

model = get_or_train_model()

# Quantile calculations
if not crop_df.empty:
    rainfall_quantiles = {
        "Low": float(crop_df["Annual_Rainfall"].quantile(0.25)),
        "Normal": float(crop_df["Annual_Rainfall"].median()),
        "High": float(crop_df["Annual_Rainfall"].quantile(0.75))
    }
    fertilizer_quantiles = {
        "Low": float(crop_df["Fertilizer"].quantile(0.25)),
        "Medium": float(crop_df["Fertilizer"].median()),
        "High": float(crop_df["Fertilizer"].quantile(0.75))
    }
    pesticide_quantiles = {
        "Low": float(crop_df["Pesticide"].quantile(0.25)),
        "Medium": float(crop_df["Pesticide"].median()),
        "High": float(crop_df["Pesticide"].quantile(0.75))
    }
else:
    rainfall_quantiles = {"Low": 600.0, "Normal": 1400.0, "High": 2200.0}
    fertilizer_quantiles = {"Low": 500000.0, "Medium": 2500000.0, "High": 10000000.0}
    pesticide_quantiles = {"Low": 1000.0, "Medium": 10000.0, "High": 50000.0}

# -----------------------------
# Request Schemas
# -----------------------------
class PredictionRequest(BaseModel):
    crop: str
    state: str
    season: str
    year: int
    area: float
    rainfall_level: str = "Normal"
    fertilizer_level: str = "Medium"
    pesticide_level: str = "Medium"

# -----------------------------
# Helper Functions
# -----------------------------
def get_season_temperature(year: int, season: str) -> float:
    if temp_df.empty:
        return 26.5
    row = temp_df[temp_df["YEAR"] == year]
    if row.empty:
        return 26.5
    tdata = row.iloc[0]
    s_lower = season.lower()
    if "kharif" in s_lower:
        return float(tdata.get("JUN-SEP", 27.0))
    elif "rabi" in s_lower:
        return float((tdata.get("OCT-DEC", 25.0) + tdata.get("JAN-FEB", 23.0)) / 2.0)
    elif "summer" in s_lower:
        return float(tdata.get("MAR-MAY", 31.0))
    elif "winter" in s_lower:
        return float(tdata.get("JAN-FEB", 23.0))
    else:
        return float(tdata.get("ANNUAL", 26.5))

# -----------------------------
# API Endpoints
# -----------------------------
@app.get("/api/options")
def get_options():
    if crop_df.empty:
        return {"crops": [], "states": [], "seasons": [], "years": []}
    
    crops = sorted(crop_df["Crop"].unique().tolist())
    states = sorted(crop_df["State"].unique().tolist())
    seasons = sorted(crop_df["Season"].unique().tolist())
    
    years = []
    if not temp_df.empty and "YEAR" in temp_df.columns:
        years = sorted(temp_df["YEAR"].unique().tolist())
    
    return {
        "crops": crops,
        "states": states,
        "seasons": seasons,
        "years": years
    }

@app.post("/api/predict")
def predict_crop_yield(req: PredictionRequest):
    start_time = time.time()
    rain_val = rainfall_quantiles.get(req.rainfall_level, rainfall_quantiles["Normal"])
    fert_val = fertilizer_quantiles.get(req.fertilizer_level, fertilizer_quantiles["Medium"])
    pest_val = pesticide_quantiles.get(req.pesticide_level, pesticide_quantiles["Medium"])
    
    temp_val = get_season_temperature(req.year, req.season)
    
    input_df = pd.DataFrame({
        "Crop": [req.crop],
        "Crop_Year": [req.year],
        "Season": [req.season],
        "State": [req.state],
        "Area": [req.area],
        "Annual_Rainfall": [rain_val],
        "Fertilizer": [fert_val],
        "Pesticide": [pest_val],
        "Season_Temperature": [temp_val]
    })
    
    # Crop and region baseline calculation
    if not crop_df.empty and req.crop in crop_df["Crop"].values:
        crop_match = crop_df[(crop_df["Crop"] == req.crop) & (crop_df["State"] == req.state)]
        if not crop_match.empty and crop_match["Yield"].mean() > 0:
            crop_base = float(crop_match["Yield"].mean())
        else:
            crop_base = float(crop_df[crop_df["Crop"] == req.crop]["Yield"].mean())
    else:
        crop_base = 2.5

    if pd.isna(crop_base) or crop_base <= 0:
        crop_base = 2.5

    # Multipliers based on input levels
    fert_mult = 1.15 if req.fertilizer_level == "High" else (0.85 if req.fertilizer_level == "Low" else 1.0)
    rain_mult = 1.10 if req.rainfall_level == "High" else (0.80 if req.rainfall_level == "Low" else 1.0)
    pest_mult = 1.05 if req.pesticide_level == "High" else (0.92 if req.pesticide_level == "Low" else 1.0)

    dynamic_estimate = crop_base * fert_mult * rain_mult * pest_mult
    engine_used = "RandomForestRegressor Pipeline (Native ML)"

    if model is not None:
        try:
            predicted_yield = float(model.predict(input_df)[0])
            if predicted_yield <= 0:
                predicted_yield = dynamic_estimate
                engine_used = "Dynamic Heuristic Multiplier (Fallback)"
        except Exception:
            predicted_yield = dynamic_estimate
            engine_used = "Dynamic Heuristic Multiplier (Fallback)"
    else:
        predicted_yield = dynamic_estimate
        engine_used = "Dynamic Heuristic Multiplier (No Model)"

    total_harvest = predicted_yield * req.area

    # Risk Calculation
    risk_score = 0
    rf_low = risk_values.get("rainfall_low", 800)
    rf_high = risk_values.get("rainfall_high", 2500)
    t_low = risk_values.get("temperature_low", 18)
    t_high = risk_values.get("temperature_high", 32)

    if rain_val < rf_low or rain_val > rf_high:
        risk_score += 1
    if temp_val < t_low or temp_val > t_high:
        risk_score += 1

    if risk_score == 0:
        risk_tier = "Low"
        risk_label = "Low Climate Risk"
        recommendation = "Favorable agricultural conditions. Maintain standard irrigation and recommended fertilizer schedule."
    elif risk_score == 1:
        risk_tier = "Medium"
        risk_label = "Moderate Risk"
        recommendation = "Weather anomalies detected. Ensure adequate drainage or localized irrigation according to soil moisture."
    else:
        risk_tier = "High"
        risk_label = "High Anomaly Risk"
        recommendation = "Unfavorable temperature or precipitation patterns. Consult agricultural advisors and adopt drought/flood mitigation."

    # Compute latency and update stats
    latency_ms = round((time.time() - start_time) * 1000, 2)
    inference_stats["count"] += 1
    inference_stats["total_latency_ms"] += latency_ms
    inference_stats["last_latency_ms"] = latency_ms
    inference_stats["last_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inference_stats["last_crop"] = req.crop
    inference_stats["last_yield"] = round(predicted_yield, 3)

    # Vivid terminal log proving background ML activity
    print("\n" + "═" * 72)
    print(f"🌾 [ML ENGINE IN BACKGROUND] Request #{inference_stats['count']} @ {inference_stats['last_timestamp']}")
    print(f"   ├─ Inputs   : Crop={req.crop} | State={req.state} | Season={req.season} | Area={req.area} ha")
    print(f"   ├─ Weather  : Rainfall={round(rain_val, 1)} mm ({req.rainfall_level}) | Temp={round(temp_val, 1)} °C")
    print(f"   ├─ Ag-Inputs: Fert={round(fert_val, 1)} kg | Pest={round(pest_val, 1)} kg")
    print(f"   ├─ Engine   : {engine_used}")
    print(f"   ├─ Output   : {round(predicted_yield, 3)} Tonnes/Ha (Total: {round(total_harvest, 2)} Tonnes)")
    print(f"   ├─ Climate  : {risk_label} [{risk_tier}]")
    print(f"   └─ Latency  : ⚡ {latency_ms} ms (Computed by Background Process)")
    print("═" * 72 + "\n", flush=True)

    return {
        "predicted_yield": round(predicted_yield, 3),
        "total_harvest": round(total_harvest, 2),
        "unit": "Tonnes/Hectare",
        "seasonal_temperature": round(temp_val, 2),
        "risk_tier": risk_tier,
        "risk_label": risk_label,
        "recommendation": recommendation,
        "engine": engine_used,
        "latency_ms": latency_ms,
        "inference_id": inference_stats["count"],
        "inputs": {
            "rainfall_mm": round(rain_val, 1),
            "fertilizer_kg": round(fert_val, 1),
            "pesticide_kg": round(pest_val, 1)
        }
    }

@app.get("/api/model-status")
def get_model_status():
    avg_lat = (
        round(inference_stats["total_latency_ms"] / inference_stats["count"], 2)
        if inference_stats["count"] > 0
        else 0.0
    )
    return {
        "status": "online",
        "model_loaded": model is not None,
        "algorithm": "RandomForestRegressor (50 Estimators)",
        "pipeline_stages": [
            "ColumnTransformer (OneHotEncoder for Crop, Season, State)",
            "Passthrough Numeric Features",
            "RandomForestRegressor"
        ],
        "features": [
            "Crop", "Crop_Year", "Season", "State", "Area",
            "Annual_Rainfall", "Fertilizer", "Pesticide", "Season_Temperature"
        ],
        "total_inferences_served": inference_stats["count"],
        "last_inference_time": inference_stats["last_timestamp"],
        "last_latency_ms": inference_stats["last_latency_ms"],
        "average_latency_ms": avg_lat,
        "process_type": "Background FastAPI Worker"
    }

@app.get("/api/analytics")
def get_analytics(crop: str = "Rice", state: str = "All"):
    if crop_df.empty:
        return {"years": [], "yields": [], "rainfall": [], "top_states": []}

    df = crop_df[crop_df["Crop"] == crop].copy()
    if state != "All":
        df = df[df["State"] == state]

    yearly = df.groupby("Crop_Year").agg({
        "Yield": "mean",
        "Annual_Rainfall": "mean"
    }).reset_index().sort_values("Crop_Year")

    top_states_df = crop_df[crop_df["Crop"] == crop].groupby("State")["Yield"].mean().reset_index()
    top_states_df = top_states_df.sort_values("Yield", ascending=False).head(8)

    return {
        "years": yearly["Crop_Year"].tolist(),
        "yields": [round(y, 2) for y in yearly["Yield"].tolist()],
        "rainfall": [round(r, 1) for r in yearly["Annual_Rainfall"].tolist()],
        "top_states": {
            "states": top_states_df["State"].tolist(),
            "yields": [round(y, 2) for y in top_states_df["Yield"].tolist()]
        }
    }

CROP_PRICES_INR = {
    "Rice": 23000, "Wheat": 22750, "Cotton(lint)": 66000, "Sugarcane": 3150,
    "Maize": 20900, "Gram": 54000, "Arhar/Tur": 70000, "Groundnut": 63000,
    "Jowar": 31800, "Bajra": 25000, "Soyabean": 46000, "Jute": 50500,
    "Potato": 18000, "Onion": 22000, "Coconut": 35000, "Barley": 18500
}

@app.get("/api/recommend")
def recommend_crops(state: str = "Punjab", season: str = "Kharif", rainfall_level: str = "Normal"):
    if crop_df.empty:
        return {"recommendations": []}
    
    crops_list = sorted(crop_df["Crop"].unique().tolist())
    r_val = rainfall_quantiles.get(rainfall_level, rainfall_quantiles.get("Normal", 1400.0))
    f_val = fertilizer_quantiles.get("Medium", 2500000.0)
    p_val = pesticide_quantiles.get("Medium", 10000.0)

    rain_mult = 1.15 if rainfall_level == "High" else (0.80 if rainfall_level == "Low" else 1.0)

    results = []
    for c in crops_list:
        cdf = pd.DataFrame({
            "Crop": [c], "Crop_Year": [2017], "Season": [season],
            "State": [state], "Area": [1.0],
            "Annual_Rainfall": [r_val], "Fertilizer": [f_val],
            "Pesticide": [p_val], "Season_Temperature": [26.5]
        })
        
        match_df = crop_df[(crop_df["State"] == state) & (crop_df["Crop"] == c)]
        if match_df.empty:
            match_df = crop_df[crop_df["Crop"] == c]

        if match_df.empty or match_df["Yield"].mean() <= 0:
            continue

        base_yield = float(match_df["Yield"].mean())

        if model is not None:
            try:
                pyield = float(model.predict(cdf)[0])
                if pyield <= 0 or pd.isna(pyield):
                    pyield = base_yield * rain_mult
            except Exception:
                pyield = base_yield * rain_mult
        else:
            pyield = base_yield * rain_mult

        p_price = CROP_PRICES_INR.get(c, 25000)
        rev = pyield * p_price
        results.append({
            "crop": c,
            "predicted_yield": round(pyield, 2),
            "estimated_revenue_inr": round(rev, 2)
        })

    results = sorted(results, key=lambda x: x["predicted_yield"], reverse=True)[:5]
    return {"recommendations": results}

# Serve static frontend web_app directory
WEB_APP_DIR = os.path.join(BASE_DIR, "web_app")
if os.path.exists(WEB_APP_DIR):
    app.mount("/static", StaticFiles(directory=WEB_APP_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(WEB_APP_DIR, "index.html"))

    @app.get("/{file_name:path}")
    def serve_static_root(file_name: str):
        file_path = os.path.join(WEB_APP_DIR, file_name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="File not found")


