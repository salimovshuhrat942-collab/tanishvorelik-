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
CHANNEL_ID = "@kanal_username" # Kanal yuzername-ini yozing
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Obuna tekshirish
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Asosiy menyu
def get_main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="👤 Profilni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalga obuna", url=GROUP_LINK)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "✨ **Tanishuv botiga xush kelibsiz!**\n\n"
        "Botdan foydalanish uchun avval kanalimizga obuna bo'ling va pastdagi tugmani bosing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga o'tish", url=GROUP_LINK)],
            [InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_sub")]
        ])
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text(
            "✅ **Rahmat! Obuna tasdiqlandi.**\n\nEndi botdan to'liq foydalanishingiz mumkin:",
            reply_markup=get_main_kb(callback.from_user.id)
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)

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
