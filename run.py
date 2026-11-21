"""
Convenience launcher for Agricultural Yield Prediction FastAPI Server.
Run: python run.py
"""

import sys
import uvicorn
from pathlib import Path

# Add backend directory to sys.path so backend modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

if __name__ == "__main__":
    print("🌾 Starting Agricultural Yield Prediction FastAPI Server...")
    print("📍 API Documentation: http://127.0.0.1:8000/docs")
    print("📍 Frontend: Open frontend/index.html in your browser")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
