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
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
GROUP_LINK = "https://t.me/+1USZgKXMKTc3YzEy"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- BAZA ---
def init_db():
    conn = sqlite3.connect("users.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS profiles 
                    (user_id INTEGER PRIMARY KEY, name TEXT, age TEXT, city TEXT, photo_id TEXT)""")
    conn.commit()
    conn.close()

init_db()

# --- HOLATLAR ---
class ProfileState(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()

# --- TUGMALAR ---
def get_main_kb(user_id):
    kb = [
        [InlineKeyboardButton(text="👤 Profilimni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalimizga obuna", url=GROUP_LINK)]
    ]
    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# --- START VA ASOSIY MENU ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "✨ **Tanishuv botiga xush kelibsiz!**\n\n"
        "Professional tanishuv muhiti. Profilingizni yarating va muloqotni boshlang.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Davom etish", callback_data="back_to_menu")]
        ])
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("✨ **Bosh menyu:**", reply_markup=get_main_kb(callback.from_user.id))

# --- PROFIL YARATISH LOGIKASI ---
@dp.callback_query(F.data == "register")
async def start_reg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("1/4 Ismingizni yozing:")
    await state.set_state(ProfileState.name)

@dp.message(ProfileState.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("2/4 Yoshingizni kiriting:")
    await state.set_state(ProfileState.age)

@dp.message(ProfileState.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("3/4 Shahringizni yozing:")
    await state.set_state(ProfileState.city)

@dp.message(ProfileState.city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("4/4 Rasmingizni yuboring:")
    await state.set_state(ProfileState.photo)

@dp.message(ProfileState.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    
    conn = sqlite3.connect("users.db")
    conn.execute("INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?, ?)",
                 (message.from_user.id, data['name'], data['age'], data['city'], photo_id))
    conn.commit()
    conn.close()
    
    await message.answer("✅ **Profilingiz muvaffaqiyatli saqlandi!**", reply_markup=get_main_kb(message.from_user.id))
    await state.clear()

# --- RANDOM TANISHUV (Like bilan) ---
@dp.callback_query(F.data == "random")
async def random_user(callback: types.CallbackQuery):
    conn = sqlite3.connect("users.db")
    user = conn.execute("SELECT * FROM profiles WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", 
                        (callback.from_user.id,)).fetchone()
    conn.close()
    
    if not user:
        await callback.answer("Hozircha boshqa foydalanuvchilar yo'q.", show_alert=True)
        return
    
    user_id, name, age, city, photo_id = user
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{user_id}")],
        [InlineKeyboardButton(text="🔄 Keyingisi", callback_data="random")],
        [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="back_to_menu")]
    ])
    
    await callback.message.answer_photo(
        photo=photo_id, 
        caption=f"👤 Ism: {name}\n🎂 Yosh: {age}\n📍 Shahar: {city}",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("like_"))
async def process_like(callback: types.CallbackQuery):
    target_id = callback.data.split("_")[1]
    try:
        user_info = await bot.get_chat(target_id)
        username = user_info.username
        if username:
            await callback.message.answer(f"❤️ **Sizga yoqdi!**\n\nFoydalanuvchi profili: @{username}")
        else:
            await callback.message.answer("❤️ **Like yuborildi!** Foydalanuvchi username'i yashirin.")
    except:
        await callback.message.answer("❌ Foydalanuvchi topilmadi.")
    await callback.answer("Like yuborildi!")

# --- ADMIN PANEL ---
@dp.callback_query(F.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ **Admin Panel**", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Rasilka", callback_data="broadcast")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
    ]))

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
