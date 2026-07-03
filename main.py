import subprocess
import sys

# Kutubxonalarni majburiy o'rnatish
def install_libraries():
    try:
        import aiogram
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram"])

install_libraries()

import asyncio
import sqlite3
import subprocess
import sys

# 1. Kutubxona tekshiruvi
try:
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram==3.17.0"])
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# SOZLAMALAR
TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
CHANNEL_ID = "@kanal_username"  # <-- KANALINGIZ @username'ini yozing
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# BAZA FUNKSIYALARI
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

init_db()

async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# TUGMALAR
def get_main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="👤 Profilimni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔄 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalga obuna", url=GROUP_LINK)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# HANDLERLAR
@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer("❌ **Botdan foydalanish uchun kanalga obuna bo'ling!**", 
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text="📢 Obuna bo'lish", url=GROUP_LINK)],
                                 [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub")]]))
        return

    conn = sqlite3.connect("users.db")
    conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    conn.close()
    await message.answer("✨ **Xush kelibsiz!** Quyidagilardan birini tanlang:", reply_markup=get_main_kb(message.from_user.id))

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text("✅ **Obuna tasdiqlandi!**", reply_markup=get_main_kb(callback.from_user.id))
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.edit_text("⚙️ **Admin Panel**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Rasilka qilish", callback_data="broadcast")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back")]
        ]))

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text("✨ **Bosh menyu:**", reply_markup=get_main_kb(callback.from_user.id))

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
