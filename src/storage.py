import json
from pathlib import Path
from datetime import datetime


def save_json(data, channel_name):
    date_str = datetime.now().strftime("%Y-%m-%d")

    base_path = Path(f"data/raw/telegram_messages/{date_str}")
    base_path.mkdir(parents=True, exist_ok=True)

    file_path = base_path / f"{channel_name}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return file_path