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

# Asosiy menyu tugmalari
def get_main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="👤 Profilni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=GROUP_LINK)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# /start komandasi
@dp.message(Command("start"))
async def start(message: types.Message):
    # Xush kelibsiz xabari va doimiy eslatma
    text = (
        "✨ **Tanishuv botiga xush kelibsiz!**\n\n"
        "Bu yerda siz yangi do'stlar topishingiz mumkin. "
        "Profil yarating va tanishuvni boshlang!\n\n"
        "📢 *Kanalimizga obuna bo'lishni unutmang: " + GROUP_LINK + "*\n"
        "Bu biz uchun katta qo'llab-quvvatlov!"
    )
    await message.answer(text, reply_markup=get_main_kb(message.from_user.id), parse_mode="Markdown")

# Admin panel tugmasi bosilganda
@dp.callback_query(F.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await callback.message.answer("⚙️ **Admin Panel**\n\nQuyidagilardan birini tanlang:", 
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="📢 Rasilka qilish", callback_data="broadcast")],
                                         [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu")]
                                     ]))
    await callback.answer()

@dp.callback_query(F.data == "menu")
async def menu(callback: types.CallbackQuery):
    await callback.message.edit_text("✨ **Bosh menyu:**", reply_markup=get_main_kb(callback.from_user.id))

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
