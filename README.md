# 🌾 Agricultural Yield Prediction and Productivity Analysis

An end-to-end Machine Learning web application to forecast agricultural crop yields.

---

## 🏗️ System Architecture

```text
Client (Browser) ─── HTTP POST ───► FastAPI Server (backend/main.py) ─── Loads ───► models/model.pkl
```

1. **Client (Browser)**: Interactive frontend interface (`frontend/index.html`) allowing users to choose crops, select a year, enter harvested land area, and view predicted yield and total production in metric tonnes.
2. **FastAPI Server (`backend/main.py`)**: High-performance REST API accepting prediction requests, applying features, and querying the ML model.
3. **ML Model (`models/model.pkl`)**: Random Forest Regressor pipeline with imputation and One-Hot Encoding trained on agricultural data.

---

## 📂 Project Structure

```text
pujitha_project/
├── backend/
│   ├── main.py              # FastAPI application & prediction endpoints
│   ├── crops.json           # Catalog of supported crop types
│   └── requirements.txt     # Python backend dependencies
├── frontend/
│   ├── index.html           # Web UI for yield prediction
│   ├── script.js            # Frontend JavaScript (API client)
│   └── style.css            # Responsive, clean styling
├── models/
│   └── model.pkl            # Trained Scikit-Learn Random Forest model
├── data/
│   ├── raw/
│   │   └── Agricultural_Yield_Final-1.csv   # Original raw dataset
│   └── processed/
│       └── cleaned_data.csv                 # Cleaned training dataset
├── notebooks/
│   └── crop_yield_prediction.ipynb          # Jupyter notebook for model training & evaluation
├── sample_inputs/
│   ├── Rice.json            # Sample test payload for Rice
│   ├── Wheat.json           # Sample test payload for Wheat
│   └── Maize_corn.json      # Sample test payload for Maize
├── results/
│   └── graphs/              # Output directory for data visualization plots
├── .gitignore               # Ignored cache and temporary files
├── Procfile                 # Cloud deployment process file
├── render.yaml              # Render Web Service blueprint
├── runtime.txt              # Cloud Python runtime version
├── README.md                # Project documentation
├── requirements.txt         # Root requirements file
└── run.py                   # Helper script to start the local server
```

---

## 🚀 Quick Start Guide

### 1. Local Development
```bash
pip install -r requirements.txt
python run.py
```
- Web UI: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## ☁️ Deployment on Render (No Database Needed!)

This project runs as a pure **Web Service** on Render with zero database dependencies:

1. Push this repository to GitHub.
2. Go to **Render Dashboard** -> **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Set:
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy Web Service** (do **NOT** add or link any database).
