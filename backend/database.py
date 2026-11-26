"""
PostgreSQL database module (Neon DB) for full CRUD operations on prediction history.
Reads connection string from the DATABASE_URL environment variable (or .env file).
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from project root if it exists
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")


def is_db_configured() -> bool:
    """Return True if DATABASE_URL is set."""
    return bool(DATABASE_URL)


def get_connection():
    """Create a PostgreSQL database connection."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db() -> bool:
    """Initialize the predictions table in PostgreSQL if it does not exist."""
    if not DATABASE_URL:
        print("Warning: DATABASE_URL not set. Database persistence is disabled.")
        return False

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        crop VARCHAR(255) NOT NULL,
                        year INTEGER NOT NULL,
                        crop_area_harvested DOUBLE PRECISION NOT NULL,
                        predicted_yield DOUBLE PRECISION NOT NULL,
                        estimated_total_production_tonnes DOUBLE PRECISION NOT NULL
                    );
                """)
            conn.commit()
        print("PostgreSQL database initialized successfully.")
        return True
    except Exception as e:
        print(f"Warning: Could not initialize PostgreSQL database: {e}")
        return False


# CREATE
def save_prediction(
    crop: str,
    year: int,
    area: float,
    predicted_yield: float,
    total_tonnes: float,
) -> Optional[int]:
    """Insert a new prediction record into PostgreSQL and return its ID."""
    if not DATABASE_URL:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO predictions (
                    crop, year, crop_area_harvested, predicted_yield, estimated_total_production_tonnes
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (crop, year, area, predicted_yield, total_tonnes),
            )
            row = cur.fetchone()
        conn.commit()
        return row["id"] if row else None


# READ (All)
def get_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve the most recent predictions from PostgreSQL."""
    if not DATABASE_URL:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                    crop,
                    year,
                    crop_area_harvested,
                    predicted_yield,
                    estimated_total_production_tonnes
                FROM predictions
                ORDER BY id DESC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [dict(row) for row in rows]


# READ (Single)
def get_prediction_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single prediction record by ID."""
    if not DATABASE_URL:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                    crop,
                    year,
                    crop_area_harvested,
                    predicted_yield,
                    estimated_total_production_tonnes
                FROM predictions
                WHERE id = %s;
                """,
                (record_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


# UPDATE
def update_prediction(
    record_id: int,
    crop: str,
    year: int,
    area: float,
    predicted_yield: float,
    total_tonnes: float,
) -> Optional[Dict[str, Any]]:
    """Update an existing prediction record by ID and return the updated row."""
    if not DATABASE_URL:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE predictions
                SET
                    crop = %s,
                    year = %s,
                    crop_area_harvested = %s,
                    predicted_yield = %s,
                    estimated_total_production_tonnes = %s
                WHERE id = %s
                RETURNING
                    id,
                    TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') AS timestamp,
                    crop,
                    year,
                    crop_area_harvested,
                    predicted_yield,
                    estimated_total_production_tonnes;
                """,
                (crop, year, area, predicted_yield, total_tonnes, record_id),
            )
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None


# DELETE (Single)
def delete_prediction(record_id: int) -> bool:
    """Delete a prediction record by ID. Returns True if a row was deleted."""
    if not DATABASE_URL:
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM predictions WHERE id = %s RETURNING id;",
                (record_id,),
            )
            row = cur.fetchone()
        conn.commit()
        return row is not None


# DELETE (All)
def clear_history() -> int:
    """Delete all prediction records and return the number of deleted rows."""
    if not DATABASE_URL:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM predictions;")
            deleted_count = cur.rowcount
        conn.commit()
        return deleted_count
