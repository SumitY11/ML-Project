import pandas as pd
import numpy as np
import joblib
import os

print("Starting native model retraining for current scikit-learn version...")

# Load datasets
crop_df = pd.read_csv("data/crop_yield.csv")
temp_df = pd.read_csv("data/temperatures.csv")

# Clean strings
for col in ["Crop", "State", "Season"]:
    crop_df[col] = crop_df[col].astype(str).str.strip()

# Compute seasonal temperature mapping for crop_df rows
def get_temp(row):
    yr = row["Crop_Year"]
    season = str(row["Season"]).lower()
    t_rows = temp_df[temp_df["YEAR"] == yr]
    if t_rows.empty:
        return 26.5
    tdata = t_rows.iloc[0]
    if "kharif" in season:
        return float(tdata.get("JUN-SEP", 27.0))
    elif "rabi" in season:
        return float((tdata.get("OCT-DEC", 25.0) + tdata.get("JAN-FEB", 23.0)) / 2.0)
    elif "summer" in season:
        return float(tdata.get("MAR-MAY", 31.0))
    elif "winter" in season:
        return float(tdata.get("JAN-FEB", 23.0))
    else:
        return float(tdata.get("ANNUAL", 26.5))

if "Season_Temperature" not in crop_df.columns:
    crop_df["Season_Temperature"] = crop_df.apply(get_temp, axis=1)

# Select features for training
features = ["Crop", "Crop_Year", "Season", "State", "Area", "Annual_Rainfall", "Fertilizer", "Pesticide", "Season_Temperature"]
X = crop_df[features]
y = crop_df["Yield"]

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor

categorical_cols = ["Crop", "Season", "State"]
numerical_cols = [c for c in features if c not in categorical_cols]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_cols),
        ("num", "passthrough", numerical_cols)
    ]
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
])

print("Fitting RandomForest model on 19,689 records...")
pipeline.fit(X, y)

os.makedirs("model", exist_ok=True)
model_path = os.path.join("model", "crop_yield_model.pkl")
joblib.dump(pipeline, model_path)
print(f"SUCCESS: Model trained and saved to {model_path}!")

# Test prediction
test_df = pd.DataFrame({
    "Crop": ["Rice"],
    "Crop_Year": [2017],
    "Season": ["Kharif"],
    "State": ["Punjab"],
    "Area": [2.5],
    "Annual_Rainfall": [1400.0],
    "Fertilizer": [2500000.0],
    "Pesticide": [10000.0],
    "Season_Temperature": [26.5]
})

test_pred = pipeline.predict(test_df)[0]
print(f"Test prediction for Rice in Punjab: {test_pred:.3f} Tonnes/Ha")
