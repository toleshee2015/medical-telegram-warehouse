import asyncio
from telegram_client import client

async def main():

    await client.start()

    me = await client.get_me()

    print("Connected Successfully!")

    print("Name:", me.first_name)

    print("Username:", me.username)

with client:
    client.loop.run_until_complete(main())