import joblib
import pandas as pd

try:
    model = joblib.load("model/crop_yield_model.pkl")
    print("Model loaded.")
    print("Model type:", type(model))
    
    if hasattr(model, "feature_names_in_"):
        print("Feature names in model:", model.feature_names_in_)
    elif hasattr(model, "named_steps"):
        pre = model.named_steps.get("preprocessor")
        if pre and hasattr(pre, "feature_names_in_"):
            print("Preprocessor feature names in:", pre.feature_names_in_)

    test_df = pd.DataFrame({
        "Crop": ["Rice"],
        "Crop_Year": [2020],
        "Season": ["Kharif"],
        "State": ["Punjab"],
        "Area": [2.5],
        "Annual_Rainfall": [1400.0],
        "Fertilizer": [2500000.0],
        "Pesticide": [10000.0],
        "Season_Temperature": [26.5]
    })
    
    print("Trying model.predict(test_df)...")
    pred = model.predict(test_df)
    print("Prediction SUCCESS! Result:", pred)

except Exception as e:
    import traceback
    print("ERROR DURING PREDICT:")
    traceback.print_exc()
