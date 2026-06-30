from pathlib import Path


def save_image(client, message, channel_name):
    if not message.photo:
        return None

    image_dir = Path(f"data/raw/images/{channel_name}")
    image_dir.mkdir(parents=True, exist_ok=True)

    file_path = image_dir / f"{message.id}.jpg"

    client.download_media(message, file=file_path)

    return str(file_path)