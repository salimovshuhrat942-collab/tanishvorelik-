# bot.py — Tanishuv Bot PRO
import asyncio
from datetime import datetime
import time

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
)

import db
from config import (
    BOT_TOKEN, ADMIN_IDS, REQUIRED_CHANNEL, MIN_AGE, MAX_AGE,
    MAX_NAME_LEN, MAX_BIO_LEN, log,
)
from locations import REGION_NAMES, get_districts
from security import (
    flood_guard, admin_only, sanitize_text, validate_age, is_subscribed,
)

router = Router()

# ============ KEYBOARDS ============

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Ko'rish")],
            [KeyboardButton(text="👤 Mening profilim"), KeyboardButton(text="💎 VIP")],
            [KeyboardButton(text="❌ Profilni o'chirish")],
        ],
        resize_keyboard=True,
    )

def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Kanallarni boshqarish", callback_data="admin_channels")],
        [InlineKeyboardButton(text="💎 VIP berish", callback_data="admin_vip")],
        [InlineKeyboardButton(text="📣 Broadcast", callback_data="admin_broadcast")]
    ])

# ============ ADMIN PANEL TUGMALARI ============

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: Message):
    await message.answer("🛠 <b>Admin boshqaruv paneli:</b>", 
                         reply_markup=admin_menu_kb(), parse_mode="HTML")

@router.callback_query(F.data == "admin_stats")
@admin_only
async def admin_stats_cb(callback: CallbackQuery):
    stats = db.get_stats()
    text = (f"📊 <b>Statistika:</b>\n\n"
            f"👥 Jami: {stats['total']}\n"
            f"✅ Faol: {stats['active']}\n"
            f"👨 Erkak: {stats['male']} | 👩 Ayol: {stats['female']}\n"
            f"❤️ Match: {stats['matches']}\n"
            f"💎 VIP: {stats['vip']}\n"
            f"🚫 Ban: {stats['banned']}")
    await callback.message.edit_text(text, reply_markup=admin_menu_kb(), parse_mode="HTML")

# ============ SETVIP (To'g'rilangan) ============

@router.message(Command("setvip"))
@admin_only
async def cmd_setvip(message: Message):
    # Foydalanish: /setvip 12345 30
    parts = message.text.split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("⚠️ Format: /setvip [user_id] [kunlar]")
        return
    
    user_id, days = int(parts[1]), int(parts[2])
    until_ts = int(time.time()) + (days * 86400)
    db.set_vip(user_id, until_ts)
    await message.answer(f"💎 {user_id} ga {days} kunlik VIP muvaffaqiyatli berildi.")

# ============ COMMANDS (Dublikatlarsiz) ============

@router.message(Command("ban"))
@admin_only
async def cmd_ban(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /ban [user_id]")
        return
    db.ban_user(int(parts[1]), True)
    await message.answer(f"🚫 {parts[1]} bloklandi.")

@router.message(Command("unban"))
@admin_only
async def cmd_unban(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /unban [user_id]")
        return
    db.ban_user(int(parts[1]), False)
    await message.answer(f"✅ {parts[1]} blokdan chiqarildi.")

# ============ MAIN ============

async def main():
    db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot ishga tushdi.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot to'xtatildi.")
