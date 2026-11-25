from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import joblib
import json
from pathlib import Path
from contextlib import asynccontextmanager

try:
    from backend.database import init_db, save_prediction, get_history, is_db_configured
except ImportError:
    from database import init_db, save_prediction, get_history, is_db_configured

# Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
CROPS_JSON_PATH = Path(__file__).resolve().parent / "crops.json"
FRONTEND_DIR = BASE_DIR / "frontend"

# Global variables for model and features
model = None
features = []
crop_names = []


def load_ml_model():
    """Load the trained machine learning pipeline and feature list."""
    global model, features, crop_names

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Trained model not found at: {MODEL_PATH}")

    saved_data = joblib.load(MODEL_PATH)
    model = saved_data["model"]
    features = saved_data["features"]

    # Compatibility shim if model was pickled with an older scikit-learn SimpleImputer
    try:
        preprocessor = model.named_steps.get("preprocessor")
        if preprocessor is not None:
            for _, transformer, _ in getattr(preprocessor, "transformers_", []):
                if hasattr(transformer, "named_steps"):
                    imputer = transformer.named_steps.get("imputer")
                    if imputer is not None and not hasattr(imputer, "_fill_dtype"):
                        if hasattr(imputer, "statistics_"):
                            imputer._fill_dtype = imputer.statistics_.dtype
    except Exception:
        pass

    # Extract crop names from the fitted preprocessor encoder
    try:
        crop_encoder = (
            model.named_steps["preprocessor"]
            .named_transformers_["cat"]
            .named_steps["encoder"]
        )
        crop_names = crop_encoder.categories_[0].tolist()
    except Exception:
        # Fallback to crops.json if available
        if CROPS_JSON_PATH.exists():
            with open(CROPS_JSON_PATH, "r", encoding="utf-8") as f:
                crop_names = json.load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    init_db()
    load_ml_model()
    yield


# Create FastAPI application
app = FastAPI(
    title="Agricultural Yield Prediction API",
    description="Predict agricultural crop yield using Machine Learning.",
    version="1.0",
    lifespan=lifespan
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Input data format with realistic default values
class CropData(BaseModel):
    crop: str = Field(default="Rice", example="Rice", description="Crop name, e.g. Rice, Wheat, Maize (corn)")
    year: int = Field(default=2014, example=2014, description="Harvest target year")
    crop_area_harvested: float = Field(default=44515890.0, example=44515890.0, description="Harvested land area in hectares")

    fertilizer__nutrient_nitrogen_n_total__agricultural_use: float = 16949600.0
    fertilizer__nutrient_nitrogen_n_total__export_quantity: float = 23776.0
    fertilizer__nutrient_nitrogen_n_total__import_quantity: float = 4180999.0
    fertilizer__nutrient_nitrogen_n_total__production: float = 12433700.0
    fertilizer__nutrient_nitrogen_n_total__use_per_area_of_cropland: float = 100.02
    fertilizer__nutrient_nitrogen_n_total__use_per_capita: float = 12.92
    fertilizer__nutrient_nitrogen_n_total__use_per_value_of_agricultural_production: float = 43.79

    fertilizer__nutrient_phosphate_p2o5_total__agricultural_use: float = 6098900.0
    fertilizer__nutrient_phosphate_p2o5_total__export_quantity: float = 20552.0
    fertilizer__nutrient_phosphate_p2o5_total__import_quantity: float = 1953601.0
    fertilizer__nutrient_phosphate_p2o5_total__production: float = 4118900.0
    fertilizer__nutrient_phosphate_p2o5_total__use_per_area_of_cropland: float = 35.99
    fertilizer__nutrient_phosphate_p2o5_total__use_per_capita: float = 4.65
    fertilizer__nutrient_phosphate_p2o5_total__use_per_value_of_agricultural_production: float = 15.76

    fertilizer__nutrient_potash_k2o_total__agricultural_use: float = 2532900.0
    fertilizer__nutrient_potash_k2o_total__export_quantity: float = 21348.0
    fertilizer__nutrient_potash_k2o_total__import_quantity: float = 2510071.0
    fertilizer__nutrient_potash_k2o_total__use_per_area_of_cropland: float = 14.95
    fertilizer__nutrient_potash_k2o_total__use_per_capita: float = 1.93
    fertilizer__nutrient_potash_k2o_total__use_per_value_of_agricultural_production: float = 6.54

    land__agricultural_land__area: float = 179728.0
    land__agriculture__area: float = 179728.0
    land__agriculture_area_under_organic_agric__area: float = 720.0
    land__arable_land__area: float = 156422.978
    land__country_area__area: float = 328726.0
    land__cropland__area: float = 169463.0
    land__inland_waters__area: float = 31407.0
    land__permanent_crops__area: float = 13040.02
    land__permanent_meadows_and_pastures__area: float = 10265.0
    land__temporary_crops__area: float = 119387.92
    land__temporary_fallow__area: float = 24851.0
    land__temporary_meadows_and_pastures__area: float = 12184.06

    pesticide__pesticides_total__use_per_value_of_agricultural_production: float = 0.1

    model_config = {
        "json_schema_extra": {
            "example": {
                "crop": "Rice",
                "year": 2014,
                "crop_area_harvested": 44515890.0,
                "fertilizer__nutrient_nitrogen_n_total__agricultural_use": 16949600.0,
                "fertilizer__nutrient_phosphate_p2o5_total__agricultural_use": 6098900.0,
                "fertilizer__nutrient_potash_k2o_total__agricultural_use": 2532900.0,
                "land__agricultural_land__area": 179728.0,
                "land__cropland__area": 169463.0,
                "pesticide__pesticides_total__use_per_value_of_agricultural_production": 0.1
            }
        }
    }


# Ready-to-use sample presets for Swagger UI
SAMPLE_PRESETS = {
    "Rice (Sample Preset)": {
        "summary": "Rice (Pre-filled sample)",
        "description": "Ready-to-test real data for Rice",
        "value": {
            "crop": "Rice",
            "year": 2014,
            "crop_area_harvested": 44515890.0,
            "fertilizer__nutrient_nitrogen_n_total__agricultural_use": 16949600.0,
            "fertilizer__nutrient_phosphate_p2o5_total__agricultural_use": 6098900.0,
            "fertilizer__nutrient_potash_k2o_total__agricultural_use": 2532900.0,
            "land__agricultural_land__area": 179728.0,
            "land__cropland__area": 169463.0,
            "pesticide__pesticides_total__use_per_value_of_agricultural_production": 0.1
        }
    },
    "Wheat (Sample Preset)": {
        "summary": "Wheat (Pre-filled sample)",
        "description": "Ready-to-test real data for Wheat",
        "value": {
            "crop": "Wheat",
            "year": 2014,
            "crop_area_harvested": 30470000.0,
            "fertilizer__nutrient_nitrogen_n_total__agricultural_use": 16949600.0,
            "fertilizer__nutrient_phosphate_p2o5_total__agricultural_use": 6098900.0,
            "fertilizer__nutrient_potash_k2o_total__agricultural_use": 2532900.0,
            "land__agricultural_land__area": 179728.0,
            "land__cropland__area": 169463.0,
            "pesticide__pesticides_total__use_per_value_of_agricultural_production": 0.1
        }
    }
}


# Serve web interface directly at root "/"
@app.get("/", include_in_schema=False)
def serve_home():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Agricultural Yield Prediction API is running!"}


@app.get("/style.css", include_in_schema=False)
def serve_css():
    return FileResponse(FRONTEND_DIR / "style.css", media_type="text/css")


@app.get("/script.js", include_in_schema=False)
def serve_js():
    return FileResponse(FRONTEND_DIR / "script.js", media_type="application/javascript")


# Health Check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database_configured": is_db_configured(),
        "features_count": len(features),
        "total_crops": len(crop_names)
    }


# API Status & Route Directory
@app.get("/api")
def api_info():
    return {
        "message": "Agricultural Yield Prediction API is running!",
        "endpoints": {
            "web_ui": "/",
            "health": "/health",
            "crops": "/crops",
            "predict": "/predict (POST)",
            "history": "/history",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


# Get available crop names
@app.get("/crops")
def get_crops():
    return {
        "total_crops": len(crop_names),
        "crops": crop_names
    }


# Predict crop yield
@app.post("/predict")
def predict(
    data: CropData = Body(
        ...,
        openapi_examples=SAMPLE_PRESETS
    )
):
    if model is None:
        raise HTTPException(status_code=500, detail="ML model is not loaded.")

    # Fallback to realistic Rice sample if Swagger default dummy values are sent
    if data.crop == "string" or not data.crop:
        data.crop = "Rice"
    if data.year <= 0:
        data.year = 2014
    if data.crop_area_harvested <= 0:
        data.crop_area_harvested = 44515890.0

    input_data = data.model_dump()
    input_df = pd.DataFrame([input_data])

    # Arrange input columns in exact training order
    try:
        input_df = input_df[features]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing feature column: {e}")

    try:
        prediction = model.predict(input_df)
        predicted_yield = float(prediction[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction failed: {str(e)}")

    rounded_yield = round(predicted_yield, 2)
    total_tonnes = round((predicted_yield * data.crop_area_harvested) / 1000.0, 2)

    record_id = None
    try:
        record_id = save_prediction(
            crop=data.crop,
            year=data.year,
            area=data.crop_area_harvested,
            predicted_yield=rounded_yield,
            total_tonnes=total_tonnes,
        )
    except Exception as e:
        print(f"Warning: Could not save prediction to PostgreSQL: {e}")

    return {
        "id": record_id,
        "crop": data.crop,
        "year": data.year,
        "crop_area_harvested": data.crop_area_harvested,
        "predicted_yield": rounded_yield,
        "yield_unit": "kg/ha",
        "estimated_total_production_tonnes": total_tonnes
    }


# Retrieve stored prediction history from PostgreSQL
@app.get("/history")
def history(limit: int = 50):
    try:
        records = get_history(limit=limit)
        return {
            "total": len(records),
            "history": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")
