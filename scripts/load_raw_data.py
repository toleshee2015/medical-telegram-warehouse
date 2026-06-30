import json
import os
from pathlib import Path

import psycopg2

# PostgreSQL connection
conn = psycopg2.connect(
    host="localhost",
    database="telegram_db",
    user="postgres",
    password="123",
    port=5432
)

cursor = conn.cursor()

DATA_FOLDER = Path("../data")


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


insert_query = """
INSERT INTO raw.telegram_messages(
    id,
    channel_name,
    channel_username,
    message_id,
    message_date,
    sender_id,
    sender_name,
    message_text,
    views,
    forwards,
    replies,
    has_media,
    media_type,
    media_path,
    raw_json
)
VALUES (
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
)
ON CONFLICT (id) DO NOTHING;
"""

for file in DATA_FOLDER.glob("*.json"):

    messages = load_json(file)

    for msg in messages:

        cursor.execute(
            insert_query,
            (
                msg.get("id"),
                msg.get("channel_name"),
                msg.get("channel_username"),
                msg.get("message_id"),
                msg.get("date"),
                msg.get("sender_id"),
                msg.get("sender_name"),
                msg.get("text"),
                msg.get("views"),
                msg.get("forwards"),
                msg.get("replies"),
                msg.get("has_media"),
                msg.get("media_type"),
                msg.get("media_path"),
                json.dumps(msg),
            ),
        )

conn.commit()

cursor.close()
conn.close()

print("Data successfully loaded.")