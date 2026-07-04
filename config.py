# config.py
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("tanishuv_bot")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    log.critical("BOT_TOKEN topilmadi! Railway Variables da BOT_TOKEN o'rnating.")
    sys.exit(1)

# ADMIN_IDS ni yanada ishonchli yuklash
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set()

if _admin_raw:
    for part in _admin_raw.split(","):
        part = part.strip()
        if part.isdigit():
            ADMIN_IDS.add(int(part))
    log.info(f"Yuklangan ADMIN_IDS: {ADMIN_IDS}")
else:
    log.warning("ADMIN_IDS muhit o'zgaruvchisi topilmadi yoki bo'sh!")

if not ADMIN_IDS:
    log.error("DIQQAT: Adminlar ro'yxati bo'sh! Admin buyruqlari ishlamaydi.")

# Majburiy obuna kanali
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()

# Ma'lumotlar bazasi yo'li
DB_PATH = os.getenv("DB_PATH", "/data/tanishuv.db")

# Profil cheklovlari
MIN_AGE = 18
MAX_AGE = 70
MAX_NAME_LEN = 40
MAX_BIO_LEN = 300
FLOOD_LIMIT_SECONDS = 1.2
