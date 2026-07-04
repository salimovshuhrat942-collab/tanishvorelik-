# config.py
# BARCHA MAXFIY MA'LUMOTLAR shu yerda emas, balki ENVIRONMENT VARIABLES orqali o'qiladi.
# Railway -> Variables bo'limida quyidagilarni kiriting:
#   BOT_TOKEN=...
#   ADMIN_IDS=123456789,987654321
#   REQUIRED_CHANNEL=@sizning_kanalingiz
#   DB_PATH=/data/tanishuv.db   (Railway Volume mount pathi bilan bir xil bo'lsin!)

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
    log.critical("BOT_TOKEN topilmadi! Railway/'.env' da BOT_TOKEN o'rnating.")
    sys.exit(1)

# Admin ID lar: "123,456" -> [123, 456]
_admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set()
for part in _admin_raw.split(","):
    part = part.strip()
    if part.isdigit():
        ADMIN_IDS.add(int(part))

if not ADMIN_IDS:
    log.warning("ADMIN_IDS bo'sh! Admin panelga hech kim kira olmaydi. "
                "Railway Variables ga ADMIN_IDS=your_telegram_id qo'shing.")

# Majburiy obuna kanali (ixtiyoriy). Bo'sh bo'lsa tekshiruv o'chiriladi.
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()  # masalan: @mening_kanalim

# Ma'lumotlar bazasi yo'li. Railway Volume mount path bilan mos bo'lishi SHART,
# aks holda har deployda ma'lumotlar o'chib ketadi.
DB_PATH = os.getenv("DB_PATH", "/data/tanishuv.db")

# Profil uchun cheklovlar (xavfsizlik / spamdan himoya)
MIN_AGE = 18
MAX_AGE = 70
MAX_NAME_LEN = 40
MAX_BIO_LEN = 300
FLOOD_LIMIT_SECONDS = 1.2  # bir foydalanuvchi ketma-ket amallar orasidagi minimal vaqt
