from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import logging

from api.database import get_db
from api.schemas import (
    TopProduct,
    ChannelActivity,
    MessageSearchResult,
    VisualContentStats
)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medical Telegram Analytics API",
    description="Analytics layer on top of dbt warehouse",
    version="1.0.0"
)

# =========================================================
# Endpoint 1: Top Products
# =========================================================

@app.get(
    "/api/reports/top-products",
    response_model=list[TopProduct],
    summary="Get most frequently mentioned products"
)
def top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:
        query = text("""
            SELECT
                UNNEST(STRING_TO_ARRAY(lower(message), ' ')) AS product,
                COUNT(*) AS count
            FROM stg_telegram_messages
            GROUP BY product
            ORDER BY count DESC
            LIMIT :limit
        """)

        result = db.execute(query, {"limit": limit}).fetchall()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No products found."
            )

        return [
            {"product": r[0], "count": r[1]}
            for r in result
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database query failed."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )


# =========================================================
# Endpoint 2: Channel Activity
# =========================================================

@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=list[ChannelActivity],
    summary="Channel posting activity over time"
)
def channel_activity(
    channel_name: str,
    db: Session = Depends(get_db)
):
    try:

        if not channel_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Channel name cannot be empty."
            )

        query = text("""
            SELECT
                date_key::text AS date,
                COUNT(*) AS message_count
            FROM fct_messages
            WHERE channel_key = :channel_name
            GROUP BY date_key
            ORDER BY date_key
        """)

        result = db.execute(
            query,
            {"channel_name": channel_name}
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No activity found for this channel."
            )

        return [
            {
                "date": r[0],
                "message_count": r[1]
            }
            for r in result
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database query failed."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )


# =========================================================
# Endpoint 3: Message Search
# =========================================================

@app.get(
    "/api/search/messages",
    response_model=list[MessageSearchResult],
    summary="Search messages by keyword"
)
def search_messages(
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    try:

        sql = text("""
            SELECT
                message_id,
                channel_key,
                message,
                date_key
            FROM stg_messages
            WHERE message ILIKE :query
            LIMIT :limit
        """)

        result = db.execute(
            sql,
            {
                "query": f"%{query}%",
                "limit": limit
            }
        ).fetchall()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No matching messages found."
            )

        return [
            {
                "message_id": r[0],
                "channel_name": r[1],
                "message": r[2],
                "date": str(r[3])
            }
            for r in result
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database query failed."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )

# =========================================================
# Endpoint 4: Visual Content Statistics
# =========================================================

@app.get(
    "/api/reports/visual-content",
    response_model=list[VisualContentStats],
    summary="Image usage statistics across channels"
)
def visual_content_stats(
    db: Session = Depends(get_db)
):
    try:

        query = text("""
            SELECT
                channel_name,
                COUNT(*) AS total_images,
                SUM(CASE WHEN image_category='promotional' THEN 1 ELSE 0 END) AS promotional,
                SUM(CASE WHEN image_category='product_display' THEN 1 ELSE 0 END) AS product_display,
                SUM(CASE WHEN image_category='lifestyle' THEN 1 ELSE 0 END) AS lifestyle,
                SUM(CASE WHEN image_category='other' THEN 1 ELSE 0 END) AS other
            FROM stg_yolo_detections
            GROUP BY channel_name
            ORDER BY total_images DESC
        """)

        result = db.execute(query).fetchall()

        if not result:
            raise HTTPException(
                status_code=404,
                detail="No visual statistics available."
            )

        return [
            {
                "channel_name": r[0],
                "total_images": r[1],
                "promotional": r[2],
                "product_display": r[3],
                "lifestyle": r[4],
                "other": r[5],
            }
            for r in result
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Database query failed."
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error."
        )