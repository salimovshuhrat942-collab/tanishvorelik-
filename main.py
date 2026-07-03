import os
os.system("pip install aiogram")

import asyncio
from aiogram import Bot, Dispatcher, types, F
# ... qolgan kodlaringiz

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Token va Admin ID
TOKEN = "8582560566:AAGd87OTCBmoSH0WQPZ2ObgP44SXwQR8mVc"
ADMIN_ID = 8007670371
REQUIRED_CHANNEL = "@kanal_username" # Kanal nomini kiriting

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

users_db = {}
user_ids = set()

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    district = State()
    photo = State()

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_ids.add(message.from_user.id)
    await message.answer(f"Xush kelibsiz! Botdan foydalanish uchun {REQUIRED_CHANNEL} ga obuna bo'ling.\n\nRo'yxatdan o'tish uchun ismingizni yozing:")
    await state.set_state(Registration.name)

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
    await message.answer("Profil yaratildi! /random buyrug'i orqali tanishuvni boshlang.")
    await state.clear()

@dp.message(Command("send"))
async def broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/send ", "")
        for uid in user_ids:
            try: await bot.send_message(uid, text)
            except: continue
        await message.answer("Xabar barchaga yuborildi.")

@dp.message(Command("random"))
async def random_user(message: types.Message):
    import random
    others = [uid for uid in users_db if uid != message.from_user.id]
    if not others:
        await message.answer("Hozircha foydalanuvchilar yo'q.")
        return
    
    target_id = random.choice(others)
    user = users_db[target_id]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{target_id}")],
        [InlineKeyboardButton(text="🔄 Keyingisi", callback_data="random")]
    ])
    
    await message.answer_photo(photo=user['photo'], 
                               caption=f"👤 {user['name']}, {user['age']} yosh\n📍 {user['city']}, {user['district']}",
                               reply_markup=kb)

@dp.callback_query(F.data.startswith("like_"))
async def like_user(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    username = users_db[target_id].get('username', 'Mavjud emas')
    await callback.message.answer(f"Sizga yoqdi! Uning profili: @{username}")
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
