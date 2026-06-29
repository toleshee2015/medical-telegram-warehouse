from dotenv import load_dotenv
import os

load_dotenv()

print("API_ID:", os.getenv("API_ID"))
print("API_HASH:", os.getenv("API_HASH"))