import subprocess
import sys

# Kutubxonalarni majburiy o'rnatish
def install_libraries():
    try:
        import aiogram
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram"])

install_libraries()

import subprocess
import sys

# Kutubxonalarni avtomatik o'rnatish
try:
    import aiogram
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram==3.17.0"])

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
CHANNEL_ID = "@kanal_username" # Kanal yuzername-ini shu yerga yozing (masalan: @tanishuv_guruhi)
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Obuna tekshirish funksiyasi
async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# Asosiy menyu
def main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="📝 Profilni to'ldirish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Start va Obuna tekshiruvi
@dp.message(Command("start"))
async def start(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=GROUP_LINK)],
            [InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")]
        ])
        await message.answer("❌ Botdan foydalanish uchun avval kanalimizga obuna bo'ling!", reply_markup=kb)
    else:
        await message.answer("✨ **Tanishuv botiga xush kelibsiz!**", reply_markup=main_kb(message.from_user.id))

# Obunani tekshirish tugmasi
@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text("✅ Obuna tasdiqlandi!", reply_markup=main_kb(callback.from_user.id))
    else:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
