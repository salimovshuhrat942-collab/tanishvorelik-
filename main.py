import os
os.system("pip install aiogram==3.17.0")

# Mana shu yerdan pastga sizning kodlaringiz davom etadi
import asyncio
from aiogram import Bot, Dispatcher, types, F
# ... qolgan kod

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8842602846:AAE1ZboKqZJe3Ie28lM2WkoqE76cDaKzES0"
ADMIN_ID = 8007670371
REQUIRED_CHANNEL = "https://"@kanal_username"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

users_db = {}
user_ids = set()

# Menyu tugmalari
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profilimni yaratish", callback_data="register")],
        [InlineKeyboardButton(text="🔄 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="📢 Kanalga obuna", url="://https://t.me/+1USZgKXMKTc3YzEy")]
    ])
    return keyboard

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    district = State()
    photo = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    user_ids.add(message.from_user.id)
    await message.answer(
        "Salom! Tanishuv botiga xush kelibsiz! Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_main_keyboard()
    )

@dp.callback_query(F.data == "register")
async def start_reg(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Ismingizni yozing:")
    await state.set_state(Registration.name)
    await callback.answer()

# --- Qolgan ro'yxatdan o'tish qismlari (oldingidek) ---
@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Yoshingizni kiriting:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Shaxringizni yozing:")
    await state.set_state(Registration.city)

@dp.message(Registration.city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Tumaningizni yozing:")
    await state.set_state(Registration.district)

@dp.message(Registration.district)
async def process_district(message: types.Message, state: FSMContext):
    await state.update_data(district=message.text)
    await message.answer("Rasmingizni yuboring:")
    await state.set_state(Registration.photo)

@dp.message(Registration.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    users_db[message.from_user.id] = {
        "name": data['name'], "age": data['age'], 
        "city": data['city'], "district": data['district'],
        "photo": message.photo[-1].file_id, "username": message.from_user.username
    }
    await message.answer("Profil yaratildi! Menyu:", reply_markup=get_main_keyboard())
    await state.clear()

@dp.callback_query(F.data == "random")
async def random_user(callback: types.CallbackQuery):
    import random
    others = [uid for uid in users_db if uid != callback.from_user.id]
    if not others:
        await callback.message.answer("Hozircha foydalanuvchilar yo'q.")
        return
    
    target_id = random.choice(others)
    user = users_db[target_id]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{target_id}")],
        [InlineKeyboardButton(text="🔄 Keyingisi", callback_data="random")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="menu")]
    ])
    
    await callback.message.answer_photo(photo=user['photo'], 
                               caption=f"👤 {user['name']}, {user['age']} yosh\n📍 {user['city']}, {user['district']}",
                               reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Bosh menyu:", reply_markup=get_main_keyboard())

@dp.callback_query(F.data.startswith("like_"))
async def like_user(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    username = users_db[target_id].get('username', 'Noma\'lum')
    await callback.message.answer(f"Sizga yoqdi! Uning profili: @{username}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
