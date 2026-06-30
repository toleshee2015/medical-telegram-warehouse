import logging
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/medical_db"
)

CSV_PATH = Path("data/processed/yolo_detections.csv")


def load_yolo_to_postgres():
    """Load YOLO detection results into PostgreSQL."""

    try:
        # Validate input file
        if not CSV_PATH.exists():
            raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

        # Read CSV
        df = pd.read_csv(CSV_PATH)

        # Validate dataframe
        if df.empty:
            raise ValueError("Input CSV is empty. Nothing to load.")

        # Create database connection
        engine = create_engine(DATABASE_URL)

        # Upload data
        df.to_sql(
            "stg_yolo_detections",
            engine,
            if_exists="replace",
            index=False
        )

        logger.info(
            "Successfully loaded %d records into 'stg_yolo_detections'.",
            len(df)
        )

    except FileNotFoundError as e:
        logger.error("Input file error: %s", e)

    except pd.errors.EmptyDataError:
        logger.error("The CSV file contains no data.")

    except SQLAlchemyError as e:
        logger.error("Database error while loading data: %s", e)

    except Exception as e:
        logger.exception("Unexpected error occurred: %s", e)
        raise


if __name__ == "__main__":
    load_yolo_to_postgres()