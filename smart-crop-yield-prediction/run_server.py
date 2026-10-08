import uvicorn
import os

if __name__ == "__main__":
    print("🌾 Starting AgriSmart Crop Yield Prediction Server...")
    print("🌐 Dashboard URL: http://localhost:8000")
    print("📡 REST API Docs: http://localhost:8000/docs")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
