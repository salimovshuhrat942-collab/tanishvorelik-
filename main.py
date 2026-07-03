import subprocess
import sys

# Kutubxonalarni majburiy o'rnatish
def install_libraries():
    try:
        import aiogram
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiogram"])

install_libraries()

# Endi qolgan kodlarimiz boshlanadi
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
# ... qolgan kodlaringiz

import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Baza yaratish
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, name TEXT, age TEXT, city TEXT, photo TEXT)""")
    conn.commit()
    conn.close()

init_db()

# Profil to'ldirish uchun holatlar
class RegState(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# Tugmalar
def main_kb(is_admin=False):
    kb = [
        [InlineKeyboardButton(text="📝 Profilni to'ldirish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Guruhga qo'shilish", url=GROUP_LINK)]
    ]
    if is_admin:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("✨ **Tanishuv botiga xush kelibsiz!**\n\nSizni qiziqarli insonlar kutmoqda. O'z profilingizni yarating va muloqotni boshlang! 👇", 
                         reply_markup=main_kb(message.from_user.id == ADMIN_ID), parse_mode="Markdown")

# Profil to'ldirish jarayoni
@dp.callback_query(F.data == "register")
async def start_reg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("1/4 👤 **Ismingizni kiriting:**")
    await state.set_state(RegState.name)

@dp.message(RegState.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("2/4 🎂 **Yoshingizni kiriting:**")
    await state.set_state(RegState.age)

@dp.message(RegState.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("3/4 📍 **Shaxringizni kiriting:**")
    await state.set_state(RegState.city)

@dp.message(RegState.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("4/4 📸 **O'zingizning chiroyli rasmingizni yuboring:**")
    await state.set_state(RegState.photo)

@dp.message(RegState.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    conn = sqlite3.connect("users.db")
    conn.execute("INSERT OR REPLACE INTO users (id, name, age, city, photo) VALUES (?, ?, ?, ?, ?)",
                 (message.from_user.id, data['name'], data['age'], data['city'], photo_id))
    conn.commit()
    conn.close()
    
    await message.answer("✅ **Profilingiz muvaffaqiyatli yaratildi!**\n\nEndi '/random' yoki tugmalar orqali tanishuvni boshlashingiz mumkin.", reply_markup=main_kb(message.from_user.id == ADMIN_ID))
    await state.clear()

# ... qolgan Random va Admin funksiyalari avvalgidek qoladi ...

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
