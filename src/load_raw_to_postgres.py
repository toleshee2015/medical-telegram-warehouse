import os
import json
from pathlib import Path
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# DB Connection
# -------------------------
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


# -------------------------
# Create schema + table
# -------------------------
def create_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;

    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
        message_id BIGINT PRIMARY KEY,
        channel_name TEXT,
        message_date TIMESTAMP,
        text TEXT,
        views INT,
        forwards INT,
        media_type TEXT,
        image_path TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()


# -------------------------
# Read JSON files
# -------------------------
def read_json_files(path="data/raw/telegram_messages"):
    base = Path(path)
    records = []

    for file in base.rglob("*.json"):
        channel_name = file.stem

        with open(file, "r", encoding="utf-8") as f:
            messages = json.load(f)

        for m in messages:
            records.append((
                m.get("message_id"),
                channel_name,
                m.get("date"),
                m.get("text"),
                m.get("views"),
                m.get("forwards"),
                m.get("media_type"),
                m.get("image_path"),
            ))

    return records


# -------------------------
# Insert into PostgreSQL
# -------------------------
def load_to_postgres(records):
    conn = get_conn()
    cur = conn.cursor()

    sql = """
    INSERT INTO raw.telegram_messages (
        message_id, channel_name, message_date,
        text, views, forwards, media_type, image_path
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (message_id) DO NOTHING;
    """

    execute_batch(cur, sql, records)

    conn.commit()
    cur.close()
    conn.close()


# -------------------------
# Main
# -------------------------
def main():
    print("Starting load...")

    create_table()
    records = read_json_files()

    print(f"Loaded {len(records)} records from JSON")

    load_to_postgres(records)

    print("Load completed successfully")


if __name__ == "__main__":
    main()