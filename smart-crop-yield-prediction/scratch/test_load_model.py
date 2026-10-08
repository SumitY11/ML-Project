import os
import joblib
import pandas as pd

MODEL_PATH = os.path.join("model", "crop_yield_model.pkl")

print(f"Testing joblib.load for: {MODEL_PATH}")
try:
    model = joblib.load(MODEL_PATH)
    print("SUCCESS: Model loaded successfully!")
    print(f"Model type: {type(model)}")
    
    # Simple test prediction
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
    pred = model.predict(test_df)
    print(f"Test prediction output: {pred[0]:.4f} Tonnes/Ha")
except Exception as e:
    print(f"FAILED to load model: {type(e).__name__}: {e}")
