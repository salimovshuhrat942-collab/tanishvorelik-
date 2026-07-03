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
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Asosiy menyu
def get_main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="👤 Profilni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalimizga obuna", url=GROUP_LINK)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: types.Message):
    # Bu yerda endi tekshiruv yo'q, shunchaki xabar va tugmalar
    await message.answer(
        "✨ **Tanishuv botiga xush kelibsiz!**\n\n"
        "Bizning kanalimizda eng qiziqarli yangiliklar va tanishuvlar!\n"
        "Obuna bo'lishni unutmang! 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga o'tish", url=GROUP_LINK)],
            [InlineKeyboardButton(text="✅ Obuna bo'ldim, davom etish", callback_data="check_sub")]
        ])
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    # Hech qanday tekshiruvsiz to'g'ridan-to'g'ri menyuni ochamiz
    await callback.message.edit_text(
        "✅ **Rahmat! Endi botdan to'liq foydalanishingiz mumkin.**",
        reply_markup=get_main_kb(callback.from_user.id)
    )

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ Admin Panel", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Rasilka", callback_data="broadcast")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
    ]))

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("✨ Bosh menyu:", reply_markup=get_main_kb(callback.from_user.id))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
