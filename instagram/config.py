import os
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_APP_ID = os.environ["INSTAGRAM_APP_ID"]
INSTAGRAM_APP_SECRET = os.environ["INSTAGRAM_APP_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]
WEBHOOK_VERIFY_TOKEN = os.environ["WEBHOOK_VERIFY_TOKEN"]
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))
DATABASE_URL = os.environ["DATABASE_URL"]
