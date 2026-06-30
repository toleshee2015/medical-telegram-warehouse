import pandas as pd
import logging
from ultralytics import YOLO
from pathlib import Path

# ==========================================================
# Logging Setup (Production Standard)
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ==========================================================
# Configuration
# ==========================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "images"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "yolo_detections.csv"

# Load YOLO model
try:
    model = YOLO("yolov8n.pt")
    logger.info("YOLO model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load YOLO model: {e}", exc_info=True)
    raise

PRODUCT_CLASSES = {
    "bottle", "cup", "wine glass", "bowl", "vase",
    "cell phone", "book", "handbag", "backpack", "sports ball"
}

# ==========================================================
# Find Images
# ==========================================================
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

image_files = [
    f for f in IMAGE_DIR.rglob("*")
    if f.is_file() and f.suffix.lower() in image_extensions
]

logger.info(f"Image directory: {IMAGE_DIR}")
logger.info(f"Total images found: {len(image_files)}")

if not image_files:
    logger.warning("No images found. Exiting pipeline safely.")
    raise SystemExit("No images found in directory")


# ==========================================================
# YOLO Detection Pipeline
# ==========================================================
results_list = []

for image_path in image_files:
    logger.info(f"Processing image: {image_path.name}")

    try:
        prediction = model(str(image_path), verbose=False)[0]

        detected_objects = []
        confidences = []

        has_person = False
        has_product = False

        # Defensive check for prediction boxes
        if prediction.boxes is not None:

            for box in prediction.boxes:
                try:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    confidence = float(box.conf[0])

                    detected_objects.append(class_name)
                    confidences.append(round(confidence, 3))

                    if class_name == "person":
                        has_person = True

                    if class_name in PRODUCT_CLASSES:
                        has_product = True

                except Exception as box_error:
                    logger.warning(
                        f"Skipping corrupted box in {image_path.name}: {box_error}"
                    )
                    continue

        # --------------------------------------------------
        # Classification logic
        # --------------------------------------------------
        if has_person and has_product:
            image_category = "promotional"
        elif has_product and not has_person:
            image_category = "product_display"
        elif has_person and not has_product:
            image_category = "lifestyle"
        else:
            image_category = "other"

        confidence_score = max(confidences) if confidences else 0

        results_list.append({
            "message_id": image_path.stem,
            "channel_name": image_path.parent.name,
            "image_name": image_path.name,
            "detected_objects": ", ".join(detected_objects),
            "confidence_score": confidence_score,
            "image_category": image_category
        })

    except Exception as e:
        logger.error(
            f"Failed processing image {image_path.name}: {e}",
            exc_info=True
        )
        continue

# ==========================================================
# Save Results Safely
# ==========================================================
try:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(results_list)

    if df.empty:
        logger.warning("No detections were generated. CSV will be empty.")

    df.to_csv(OUTPUT_CSV, index=False)

    logger.info("YOLO detection completed successfully")
    logger.info(f"Images processed: {len(image_files)}")
    logger.info(f"Rows saved: {len(df)}")
    logger.info(f"CSV saved at: {OUTPUT_CSV}")

except Exception as e:
    logger.error(f"Failed to save CSV output: {e}", exc_info=True)
    raise