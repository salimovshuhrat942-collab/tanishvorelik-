# security.py
# Botni buzishga urinishlardan himoya: flood control, admin whitelist,
# matn sanitizatsiyasi (Markdown/HTML injection oldini olish), obuna tekshiruvi.

import time
import re
import html
from functools import wraps
from aiogram import types
from config import ADMIN_IDS, REQUIRED_CHANNEL, FLOOD_LIMIT_SECONDS, log

# --- Flood control (oddiy, xotirada saqlanadigan) ---
_last_action_time: dict[int, float] = {}


def is_flooding(user_id: int) -> bool:
    now = time.time()
    last = _last_action_time.get(user_id, 0)
    _last_action_time[user_id] = now
    return (now - last) < FLOOD_LIMIT_SECONDS


def flood_guard(handler):
    """Handler decoratori: juda tez-tez bosilgan tugmalarni bloklaydi."""
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if is_flooding(user_id):
            if isinstance(event, types.CallbackQuery):
                await event.answer("Iltimos biroz kuting...", show_alert=False)
            return
        return await handler(event, *args, **kwargs)
    return wrapper


# --- Admin himoyasi ---

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def admin_only(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            log.warning(f"Ruxsatsiz admin urinishi: user_id={message.from_user.id}")
            return  # jim javob bermaymiz — botning admin buyruqlari borligini oshkor qilmaymiz
        return await handler(message, *args, **kwargs)
    return wrapper


# --- Matn sanitizatsiyasi ---

_MAX_TEXT_LEN_HARD_CAP = 500


def sanitize_text(raw: str, max_len: int) -> str:
    """
    Foydalanuvchi matnini boshqa foydalanuvchilarga ko'rsatishdan oldin tozalaydi:
    - uzunlikni cheklaydi
    - HTML/Markdown maxsus belgilarini zararsizlantiradi (parse-mode injection oldini oladi)
    - boshqaruvchi belgilarni olib tashlaydi
    """
    if raw is None:
        return ""
    raw = raw.strip()[: min(max_len, _MAX_TEXT_LEN_HARD_CAP)]
    raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)  # control chars
    return html.escape(raw)


def validate_age(text: str, min_age: int, max_age: int):
    if not text.isdigit():
        return None
    age = int(text)
    if min_age <= age <= max_age:
        return age
    return None


# --- Majburiy obuna tekshiruvi (bir nechta kanal/guruh, admin panel orqali sozlanadi) ---

async def get_missing_channels(bot, user_id: int, channels: list[str]) -> list[str]:
    """Foydalanuvchi hali a'zo bo'lmagan kanal/guruhlar ro'yxatini qaytaradi."""
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception as e:
            log.warning(f"Obuna tekshiruvida xato ({ch}): {e}. "
                        f"Bot shu kanal/guruhda admin ekanligini tekshiring.")
            # Kanal noto'g'ri sozlangan/bot admin bo'lmasa, o'sha kanalni bloklovchi qilib
            # hisoblamaymiz — butun botni ishlamay qolishidan saqlaymiz.
            continue
    return missing


async def is_subscribed(bot, user_id: int, channels: list[str] = None) -> bool:
    if channels is None:
        channels = [REQUIRED_CHANNEL] if REQUIRED_CHANNEL else []
    if not channels:
        return True
    missing = await get_missing_channels(bot, user_id, channels)
    return len(missing) == 0
