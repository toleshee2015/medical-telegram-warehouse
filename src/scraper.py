import os
import json
import logging
from datetime import datetime

from telethon.errors import FloodWaitError
from telegram_client import client

# Public Telegram channels to scrape
# Replace "CheMed" with the actual CheMed channel username if needed.
CHANNELS = [
    "lobelia4cosmetics",
    "tikvahpharma",
    "tolesheeme"
]

RAW_ROOT = "data/raw"
IMAGE_ROOT = os.path.join(RAW_ROOT, "images")
MESSAGE_ROOT = os.path.join(RAW_ROOT, "telegram_messages")

os.makedirs(IMAGE_ROOT, exist_ok=True)
os.makedirs(MESSAGE_ROOT, exist_ok=True)
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


async def scrape_channel(channel):

    logging.info(f"Started scraping {channel}")

    today = datetime.now().strftime("%Y-%m-%d")

    json_dir = os.path.join(MESSAGE_ROOT, today)
    os.makedirs(json_dir, exist_ok=True)

    image_dir = os.path.join(IMAGE_ROOT, channel)
    os.makedirs(image_dir, exist_ok=True)

    messages = []

    async for message in client.iter_messages(channel):

        media_path = None

        if message.photo:

            image_file = os.path.join(
                image_dir,
                f"{message.id}.jpg"
            )

            try:
                media_path = await client.download_media(
                    message,
                    file=image_file
                )
            except Exception as e:
                logging.error(
                    f"Image download failed ({channel}-{message.id}): {e}"
                )

        record = {
            "channel": channel,
            "message_id": message.id,
            "date": message.date.isoformat() if message.date else None,
            "text": message.text,
            "views": message.views,
            "forwards": message.forwards,
            "media_path": media_path,
            "raw": message.to_dict()
        }

        messages.append(record)

    json_file = os.path.join(
        json_dir,
        f"{channel}.json"
    )

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            messages,
            f,
            ensure_ascii=False,
            indent=4,
            default=str
        )

    logging.info(
        f"{channel}: {len(messages)} messages saved."
    )

    print(f"Finished scraping {channel}")


async def main():

    await client.start()
async def main():

    await client.start()

    me = await client.get_me()

    print("Login Successful!")
    print(f"Name: {me.first_name}")
    print(f"Username: {me.username}")

    for channel in CHANNELS:
        await scrape_channel(channel)
    me = await client.get_me()

    print("-------------------------------------")
    print("Logged in Successfully")
    print(f"Name      : {me.first_name}")
    print(f"Username  : {me.username}")
    print("-------------------------------------")

    # Optional verification of your expected username
    if me.username == "tolesheemee":
        print("Authenticated as your Telegram account.")
    else:
        print(f"Authenticated as @{me.username}, not @tolesheemee")

    logging.info(f"Logged in as @{me.username}")

    for channel in CHANNELS:

        try:
            await scrape_channel(channel)

        except FloodWaitError as e:
            logging.warning(
                f"FloodWaitError while scraping {channel}. Wait {e.seconds} seconds."
            )

        except Exception as e:
            logging.exception(
                f"Error scraping {channel}: {e}"
            )


with client:
    client.loop.run_until_complete(main())