from telegram_client import client

async def main():

    await client.start()

    async for dialog in client.iter_dialogs():
        print(dialog.name)

with client:
    client.loop.run_until_complete(main())