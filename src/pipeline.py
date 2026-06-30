import os
import subprocess
import sys
import logging
from dagster import Definitions, job, op, schedule

# =========================================================
# CONFIGURATION
# =========================================================

PYTHON_EXE = sys.executable

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =========================================================
# SAFE SUBPROCESS RUNNER (NEW - CENTRALIZED ERROR HANDLING)
# =========================================================

def run_command(command, cwd=None):
    """
    Centralized subprocess execution with:
    - consistent error handling
    - logging
    - failure visibility
    """
    try:
        logger.info(f"Executing command: {' '.join(command)}")

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            shell=False  # safer default
        )

        if result.stdout:
            logger.info(result.stdout)

        if result.returncode != 0:
            logger.error(result.stderr)
            raise RuntimeError(result.stderr)

        return result.stdout

    except Exception as e:
        logger.exception("Command execution failed")
        raise RuntimeError(f"Subprocess execution failed: {str(e)}")


# =========================================================
# OP 1: Scrape Telegram Data
# =========================================================

@op
def scrape_telegram_data():
    logger.info("Starting Telegram scraping step")

    scraper_path = os.path.join("src", "scraper.py")

    if not os.path.exists(scraper_path):
        raise FileNotFoundError(f"Scraper not found: {scraper_path}")

    run_command([PYTHON_EXE, scraper_path])

    return "scrape_complete"


# =========================================================
# OP 2: Load Raw Data into PostgreSQL
# =========================================================

@op
def load_raw_to_postgres(upstream_status: str):
    logger.info(f"Scraper status received: {upstream_status}")

    if upstream_status != "scrape_complete":
        raise ValueError("Invalid upstream state: scraping not completed")

    loader_path = os.path.join("src", "load_to_postgres.py")

    if not os.path.exists(loader_path):
        raise FileNotFoundError(f"Loader not found: {loader_path}")

    run_command([PYTHON_EXE, loader_path])

    return "load_complete"


# =========================================================
# OP 3: Run dbt Transformations
# =========================================================

@op
def run_dbt_transformations(upstream_status: str):
    logger.info(f"Load status received: {upstream_status}")

    if upstream_status != "load_complete":
        raise ValueError("Invalid upstream state: load not completed")

    dbt_cwd = os.path.abspath("dbt")

    if not os.path.exists(dbt_cwd):
        raise FileNotFoundError("dbt directory not found")

    run_command(["dbt", "run"], cwd=dbt_cwd)

    return "dbt_complete"


# =========================================================
# OP 4: Run YOLO Enrichment
# =========================================================

@op
def run_yolo_enrichment(upstream_status: str):
    logger.info(f"dbt status received: {upstream_status}")

    if upstream_status != "dbt_complete":
        raise ValueError("Invalid upstream state: dbt not completed")

    yolo_path = os.path.join("src", "yolo_detect.py")

    if not os.path.exists(yolo_path):
        raise FileNotFoundError(f"YOLO script not found: {yolo_path}")

    run_command([PYTHON_EXE, yolo_path])

    return "yolo_complete"


# =========================================================
# DAG / JOB GRAPH
# =========================================================

@job
def telegram_analytics_pipeline():
    raw = scrape_telegram_data()
    loaded = load_raw_to_postgres(raw)
    dbt_out = run_dbt_transformations(loaded)
    run_yolo_enrichment(dbt_out)


# =========================================================
# SCHEDULE
# =========================================================

@schedule(
    job=telegram_analytics_pipeline,
    cron_schedule="0 2 * * *",
    execution_timezone="Africa/Addis_Ababa"
)
def daily_schedule(_context):
    return {}

# =========================================================
# DAGSTER DEFINITIONS
# =========================================================

defs = Definitions(
    jobs=[telegram_analytics_pipeline],
    schedules=[daily_schedule]
)