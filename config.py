import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_ID_RAW = os.getenv("API_ID", "").strip()
API_ID = int(API_ID_RAW) if API_ID_RAW.isdigit() else 0
API_HASH = os.getenv("API_HASH", "").strip()

STORAGE_CHANNEL_ID_RAW = os.getenv("STORAGE_CHANNEL_ID", "").strip()
STORAGE_CHANNEL_ID = int(STORAGE_CHANNEL_ID_RAW) if STORAGE_CHANNEL_ID_RAW.lstrip("-").isdigit() else 0

ADMIN_ID_RAW = os.getenv("ADMIN_ID", "").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 7141955036
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "bd182e04").strip()

DB_PATH = BASE_DIR / "doramas.db"
TEMP_DIR = BASE_DIR / "temp_downloads"
TEMP_DIR.mkdir(exist_ok=True)


def validate_bot_config():
    errors = []
    if not BOT_TOKEN or "xxxx" in BOT_TOKEN:
        errors.append("BOT_TOKEN sozlanmagan (.env faylini to'ldiring)")
    if not STORAGE_CHANNEL_ID or STORAGE_CHANNEL_ID == -1000000000000:
        errors.append("STORAGE_CHANNEL_ID sozlanmagan (.env faylini to'ldiring)")
    return errors


def validate_uploader_config():
    errors = []
    if not API_ID:
        errors.append("API_ID sozlanmagan (.env faylini to'ldiring)")
    if not API_HASH or "abcdef" in API_HASH:
        errors.append("API_HASH sozlanmagan (.env faylini to'ldiring)")
    if not STORAGE_CHANNEL_ID or STORAGE_CHANNEL_ID == -1000000000000:
        errors.append("STORAGE_CHANNEL_ID sozlanmagan (.env faylini to'ldiring)")
    return errors
