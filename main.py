import asyncio
import os
import sqlite3
import logging
from datetime import datetime

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

# ============================================================
#              SOZLAMALAR (.env FAYLDAN O'QILADI)
# ============================================================
load_dotenv()  # loyihaning ildizidagi .env faylini o'qiydi

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi! .env faylida yoki Railway Variables'da BOT_TOKEN ni kiriting.")

# ADMIN_IDS: bitta yoki bir nechta ID, vergul bilan: ADMIN_IDS=123456789,987654321
_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().isdigit()]

# REQUIRED_CHANNEL: majburiy obuna kanali/guruhi, masalan @yoryor_rasmi
_required_channel = os.getenv("REQUIRED_CHANNEL", "").strip()
REQUIRED_CHANNELS = []
if _required_channel:
    REQUIRED_CHANNELS = [{
        "chat_id": _required_channel,
        "title": "Kanalimiz",
        "url": f"https://t.me/{_required_channel.lstrip('@')}"
    }]

DB_PATH = os.getenv("DB_PATH", "./data/tanishuv.db")
# DB_PATH papkasi mavjud bo'lmasa, avtomatik yaratamiz (masalan ./data)
_db_dir = os.path.dirname(DB_PATH)
if _db_dir and not os.path.exists(_db_dir):
    os.makedirs(_db_dir, exist_ok=True)


# ============================================================
#            O'ZBEKISTON VILOYATLARI VA TUMANLARI
# ============================================================
REGIONS = [
    ("Qoraqalpog'iston Respublikasi", [
        "Nukus shahri", "Amudaryo tumani", "Beruniy tumani", "Kegeyli tumani",
        "Qonliko'l tumani", "Qorao'zak tumani", "Qo'ng'irot tumani", "Mo'ynoq tumani",
        "Nukus tumani", "Taxiatosh tumani", "Taxtako'pir tumani", "To'rtko'l tumani",
        "Xo'jayli tumani", "Chimboy tumani", "Sho'manoy tumani", "Ellikqal'a tumani",
    ]),
    ("Andijon viloyati", [
        "Andijon shahri", "Xonabod shahri", "Andijon tumani", "Asaka tumani",
        "Baliqchi tumani", "Bo'z tumani", "Buloqboshi tumani", "Jalaquduq tumani",
        "Izboskan tumani", "Qo'rg'ontepa tumani", "Marhamat tumani", "Oltinko'l tumani",
        "Paxtaobod tumani", "Ulug'nor tumani", "Xo'jaobod tumani", "Shahrixon tumani",
    ]),
    ("Buxoro viloyati", [
        "Buxoro shahri", "Kogon shahri", "Buxoro tumani", "Vobkent tumani",
        "Jondor tumani", "Kogon tumani", "Olot tumani", "Peshku tumani",
        "Romitan tumani", "Shofirkon tumani", "Qorovulbozor tumani", "Qorako'l tumani",
        "G'ijduvon tumani",
    ]),
    ("Jizzax viloyati", [
        "Jizzax shahri", "Arnasoy tumani", "Baxmal tumani", "Do'stlik tumani",
        "Zarbdor tumani", "Zafarobod tumani", "Zomin tumani", "Mirzacho'l tumani",
        "Paxtakor tumani", "Forish tumani", "Sharof Rashidov tumani", "G'allaorol tumani",
        "Yangiobod tumani",
    ]),
    ("Qashqadaryo viloyati", [
        "Qarshi shahri", "Shahrisabz shahri", "Dehqonobod tumani", "Kasbi tumani",
        "Kitob tumani", "Koson tumani", "Mirishkor tumani", "Muborak tumani",
        "Nishon tumani", "Chiroqchi tumani", "Shahrisabz tumani", "Yakkabog' tumani",
        "Qamashi tumani", "Qarshi tumani", "G'uzor tumani",
    ]),
    ("Navoiy viloyati", [
        "Navoiy shahri", "Zarafshon shahri", "Karmana tumani", "Konimex tumani",
        "Navbahor tumani", "Nurota tumani", "Tomdi tumani", "Uchquduq tumani",
        "Xatirchi tumani", "Qiziltepa tumani",
    ]),
    ("Namangan viloyati", [
        "Namangan shahri", "Kosonsoy tumani", "Mingbuloq tumani", "Namangan tumani",
        "Norin tumani", "Pop tumani", "To'raqo'rg'on tumani", "Uychi tumani",
        "Uchqo'rg'on tumani", "Chortoq tumani", "Chust tumani", "Yangiqo'rg'on tumani",
    ]),
    ("Samarqand viloyati", [
        "Samarqand shahri", "Kattaqo'rg'on shahri", "Bulung'ur tumani", "Jomboy tumani",
        "Ishtixon tumani", "Kattaqo'rg'on tumani", "Narpay tumani", "Nurobod tumani",
        "Oqdaryo tumani", "Payariq tumani", "Pastdarg'om tumani", "Paxtachi tumani",
        "Samarqand tumani", "Toyloq tumani", "Urgut tumani", "Qo'shrabot tumani",
    ]),
    ("Surxondaryo viloyati", [
        "Termiz shahri", "Angor tumani", "Boysun tumani", "Denov tumani",
        "Jarqo'rg'on tumani", "Muzrobod tumani", "Oltinsoy tumani", "Sariosiyo tumani",
        "Termiz tumani", "Uzun tumani", "Sherobod tumani", "Sho'rchi tumani",
        "Qiziriq tumani", "Qumqo'rg'on tumani", "Bandixon tumani",
    ]),
    ("Sirdaryo viloyati", [
        "Guliston shahri", "Yangiyer shahri", "Shirin shahri", "Boyovut tumani",
        "Guliston tumani", "Mirzaobod tumani", "Oqoltin tumani", "Sardoba tumani",
        "Sayxunobod tumani", "Sirdaryo tumani", "Xovos tumani",
    ]),
    ("Toshkent viloyati", [
        "Nurafshon shahri", "Angren shahri", "Bekobod shahri", "Olmaliq shahri",
        "Ohangaron shahri", "Chirchiq shahri", "Yangiyo'l shahri", "Bekobod tumani",
        "Bo'ka tumani", "Bo'stonliq tumani", "Zangiota tumani", "Qibray tumani",
        "Quyichirchiq tumani", "Oqqo'rg'on tumani", "Ohangaron tumani", "Parkent tumani",
        "Piskent tumani", "Toshkent tumani", "O'rtachirchiq tumani", "Chinoz tumani",
        "Yuqorichirchiq tumani", "Yangiyo'l tumani",
    ]),
    ("Farg'ona viloyati", [
        "Farg'ona shahri", "Marg'ilon shahri", "Quvasoy shahri", "Qo'qon shahri",
        "Beshariq tumani", "Bog'dod tumani", "Buvayda tumani", "Dang'ara tumani",
        "Yozyovon tumani", "Quva tumani", "Qo'shtepa tumani", "Oltiariq tumani",
        "Rishton tumani", "So'x tumani", "Toshloq tumani", "O'zbekiston tumani",
        "Uchko'prik tumani", "Farg'ona tumani", "Furqat tumani",
    ]),
    ("Xorazm viloyati", [
        "Urganch shahri", "Xiva shahri", "Bog'ot tumani", "Gurlan tumani",
        "Urganch tumani", "Xiva tumani", "Xonqa tumani", "Hazorasp tumani",
        "Shovot tumani", "Yangiariq tumani", "Yangibozor tumani", "Qo'shko'pir tumani",
        "Tuproqqal'a tumani",
    ]),
    ("Toshkent shahri", [
        "Bektemir tumani", "Mirzo Ulug'bek tumani", "Mirobod tumani", "Olmazor tumani",
        "Sirg'ali tumani", "Uchtepa tumani", "Chilonzor tumani", "Shayxontohur tumani",
        "Yunusobod tumani", "Yakkasaroy tumani", "Yashnobod tumani", "Yangihayot tumani",
    ]),
]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# MUHIM: bot guruhda admin bo'lgani uchun (majburiy obunani tekshirish uchun),
# Telegram uni guruhdagi BARCHA xabarlarni ko'radigan qilib qo'yadi.
# Shu sabab botni faqat SHAXSIY chatlarda ishlaydigan qilib cheklaymiz,
# aks holda bot guruhga xabar yozib yubora boshlaydi.
dp.message.filter(F.chat.type == "private")


# ============================================================
#                          BAZA
# ============================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS profiles (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        name TEXT,
        age TEXT,
        gender TEXT,
        city TEXT,
        photo_id TEXT,
        is_banned INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS likes (
        from_id INTEGER,
        to_id INTEGER,
        created_at TEXT,
        PRIMARY KEY (from_id, to_id)
    )""")
    conn.commit()
    conn.close()


init_db()


def db_add_user_if_missing(user: types.User):
    conn = get_conn()
    row = conn.execute("SELECT user_id FROM profiles WHERE user_id=?", (user.id,)).fetchone()
    if not row:
        conn.execute(
            "INSERT INTO profiles (user_id, username, created_at) VALUES (?, ?, ?)",
            (user.id, user.username, datetime.now().isoformat())
        )
        conn.commit()
    conn.close()


def db_save_profile(user_id: int, username: str, data: dict):
    conn = get_conn()
    conn.execute("""INSERT INTO profiles (user_id, username, name, age, gender, city, photo_id, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                     ON CONFLICT(user_id) DO UPDATE SET
                        username=excluded.username,
                        name=excluded.name,
                        age=excluded.age,
                        gender=excluded.gender,
                        city=excluded.city,
                        photo_id=excluded.photo_id""",
                 (user_id, username, data['name'], data['age'], data['gender'], data['city'],
                  data['photo'], datetime.now().isoformat()))
    conn.commit()
    conn.close()


def db_get_profile(user_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row


def db_random_profile(exclude_id: int, wanted_gender: str = None):
    conn = get_conn()
    if wanted_gender:
        row = conn.execute("""SELECT * FROM profiles
                               WHERE user_id != ? AND is_banned = 0 AND name IS NOT NULL AND gender = ?
                               ORDER BY RANDOM() LIMIT 1""", (exclude_id, wanted_gender)).fetchone()
    else:
        row = conn.execute("""SELECT * FROM profiles
                               WHERE user_id != ? AND is_banned = 0 AND name IS NOT NULL
                               ORDER BY RANDOM() LIMIT 1""", (exclude_id,)).fetchone()
    conn.close()
    return row


def db_add_like(from_id: int, to_id: int) -> bool:
    """Like qo'shadi, agar ikkalasi ham bir-birini like qilgan bo'lsa True (match) qaytaradi."""
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO likes (from_id, to_id, created_at) VALUES (?, ?, ?)",
                 (from_id, to_id, datetime.now().isoformat()))
    conn.commit()
    mutual = conn.execute("SELECT 1 FROM likes WHERE from_id=? AND to_id=?", (to_id, from_id)).fetchone()
    conn.close()
    return bool(mutual)


def db_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) c FROM profiles WHERE name IS NOT NULL").fetchone()['c']
    banned = conn.execute("SELECT COUNT(*) c FROM profiles WHERE is_banned=1").fetchone()['c']
    likes = conn.execute("SELECT COUNT(*) c FROM likes").fetchone()['c']
    today = datetime.now().date().isoformat()
    today_new = conn.execute(
        "SELECT COUNT(*) c FROM profiles WHERE date(created_at)=? AND name IS NOT NULL", (today,)
    ).fetchone()['c']
    conn.close()
    return {"total": total, "banned": banned, "likes": likes, "today": today_new}


def db_all_user_ids():
    conn = get_conn()
    rows = conn.execute("SELECT user_id FROM profiles WHERE is_banned=0").fetchall()
    conn.close()
    return [r['user_id'] for r in rows]


def db_set_ban(user_id: int, banned: bool):
    conn = get_conn()
    conn.execute("UPDATE profiles SET is_banned=? WHERE user_id=?", (1 if banned else 0, user_id))
    conn.commit()
    conn.close()


def db_delete_profile(user_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM profiles WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


# ============================================================
#                        HOLATLAR (FSM)
# ============================================================
class ProfileState(StatesGroup):
    name = State()
    age = State()
    gender = State()
    region = State()
    district = State()
    photo = State()


class AdminState(StatesGroup):
    broadcast = State()
    ban_user = State()
    unban_user = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
#                       MAJBURIY OBUNA
# ============================================================
async def get_not_subscribed(user_id: int) -> list:
    """Foydalanuvchi obuna bo'lmagan kanallar ro'yxatini qaytaradi."""
    if not REQUIRED_CHANNELS:
        return []
    missing = []
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except TelegramBadRequest:
            # bot kanalda admin emas yoki kanal topilmadi — xatoni yashirmaslik uchun log qilamiz
            logging.warning(f"Obuna tekshirilmadi: {ch['chat_id']}")
            missing.append(ch)
    return missing


def subscribe_kb(missing_channels: list) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch['url'])] for ch in missing_channels]
    kb.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


async def require_subscription(target) -> bool:
    """target — Message yoki CallbackQuery. True bo'lsa davom etsa bo'ladi."""
    user_id = target.from_user.id
    missing = await get_not_subscribed(user_id)
    if missing:
        text = "⚠️ Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:"
        if isinstance(target, types.CallbackQuery):
            await target.message.answer(text, reply_markup=subscribe_kb(missing))
            await target.answer()
        else:
            await target.answer(text, reply_markup=subscribe_kb(missing))
        return False
    return True


@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: types.CallbackQuery):
    missing = await get_not_subscribed(callback.from_user.id)
    if missing:
        await callback.answer("❌ Hali barcha kanallarga obuna bo'lmadingiz.", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer("✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
                                   reply_markup=get_main_kb(callback.from_user.id))


# ============================================================
#                        TUGMALAR
# ============================================================
def get_main_kb(user_id: int) -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="👤 Profilimni yaratish/tahrirlash", callback_data="register")],
        [InlineKeyboardButton(text="🔎 Tanishuvni boshlash", callback_data="random")],
        [InlineKeyboardButton(text="🪪 Profilim", callback_data="my_profile")],
    ]
    if is_admin(user_id):
        kb.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Erkak", callback_data="gender_male"),
         InlineKeyboardButton(text="👩 Ayol", callback_data="gender_female")]
    ])


def region_kb() -> InlineKeyboardMarkup:
    kb, row = [], []
    for i, (name, _) in enumerate(REGIONS):
        row.append(InlineKeyboardButton(text=name, callback_data=f"region_{i}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)


def district_kb(region_idx: int) -> InlineKeyboardMarkup:
    districts = REGIONS[region_idx][1]
    kb, row = [], []
    for i, d in enumerate(districts):
        row.append(InlineKeyboardButton(text=d, callback_data=f"district_{i}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(text="🔙 Viloyatni qayta tanlash", callback_data="back_to_region")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Xabar yuborish (rasilka)", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⛔ Foydalanuvchini bloklash", callback_data="admin_ban")],
        [InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data="admin_unban")],
        [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")],
    ])


# ============================================================
#                     START / BOSH MENYU
# ============================================================
@dp.message(CommandStart())
async def start(message: types.Message):
    db_add_user_if_missing(message.from_user)
    if not await require_subscription(message):
        return
    await message.answer(
        "✨ <b>Tanishuv botiga xush kelibsiz!</b>\n\n"
        "Professional tanishuv muhiti. Profilingizni yarating va muloqotni boshlang.",
        parse_mode="HTML",
        reply_markup=get_main_kb(message.from_user.id)
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if not await require_subscription(callback):
        return
    try:
        await callback.message.edit_text("✨ <b>Bosh menyu:</b>", parse_mode="HTML",
                                          reply_markup=get_main_kb(callback.from_user.id))
    except TelegramBadRequest:
        await callback.message.answer("✨ <b>Bosh menyu:</b>", parse_mode="HTML",
                                       reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


# ============================================================
#                  PROFIL YARATISH LOGIKASI
# ============================================================
@dp.callback_query(F.data == "register")
async def start_reg(callback: types.CallbackQuery, state: FSMContext):
    if not await require_subscription(callback):
        return
    await callback.message.answer("1/6 Ismingizni yozing:")
    await state.set_state(ProfileState.name)
    await callback.answer()


@dp.message(ProfileState.name)
async def get_name(message: types.Message, state: FSMContext):
    if not message.text or len(message.text) > 50:
        await message.answer("❌ Iltimos, to'g'ri ism kiriting (50 belgidan kam):")
        return
    await state.update_data(name=message.text)
    await message.answer("2/6 Yoshingizni kiriting (raqamda):")
    await state.set_state(ProfileState.age)


@dp.message(ProfileState.age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text or not message.text.isdigit() or not (14 <= int(message.text) <= 99):
        await message.answer("❌ Iltimos, yoshingizni to'g'ri raqamda kiriting (masalan: 22):")
        return
    await state.update_data(age=message.text)
    await message.answer("3/6 Jinsingizni tanlang:", reply_markup=gender_kb())
    await state.set_state(ProfileState.gender)


@dp.callback_query(ProfileState.gender, F.data.startswith("gender_"))
async def get_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = "Erkak" if callback.data == "gender_male" else "Ayol"
    await state.update_data(gender=gender)
    await callback.message.answer("4/6 Viloyatingizni tanlang:", reply_markup=region_kb())
    await state.set_state(ProfileState.region)
    await callback.answer()


@dp.callback_query(ProfileState.region, F.data.startswith("region_"))
async def get_region(callback: types.CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    region_name, _ = REGIONS[idx]
    await state.update_data(region_idx=idx, region_name=region_name)
    await callback.message.edit_text(
        f"Viloyat: {region_name}\n\n5/6 Tumaningizni/shahringizni tanlang:",
        reply_markup=district_kb(idx)
    )
    await state.set_state(ProfileState.district)
    await callback.answer()


@dp.callback_query(ProfileState.district, F.data == "back_to_region")
async def back_to_region(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("4/6 Viloyatingizni tanlang:", reply_markup=region_kb())
    await state.set_state(ProfileState.region)
    await callback.answer()


@dp.callback_query(ProfileState.district, F.data.startswith("district_"))
async def get_district(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = int(callback.data.split("_")[1])
    region_idx = data['region_idx']
    district_name = REGIONS[region_idx][1][idx]
    city_value = f"{district_name}, {data['region_name']}"
    await state.update_data(city=city_value)
    await callback.message.edit_text(f"📍 Tanlandi: {city_value}")
    await callback.message.answer("6/6 Endi rasmingizni yuboring:")
    await state.set_state(ProfileState.photo)
    await callback.answer()


@dp.message(ProfileState.photo, F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data['photo'] = message.photo[-1].file_id
    db_save_profile(message.from_user.id, message.from_user.username, data)
    await message.answer("✅ <b>Profilingiz muvaffaqiyatli saqlandi!</b>", parse_mode="HTML",
                          reply_markup=get_main_kb(message.from_user.id))
    await state.clear()


@dp.message(ProfileState.photo)
async def get_photo_invalid(message: types.Message):
    await message.answer("❌ Iltimos, rasm (foto) ko'rinishida yuboring:")


# ============================================================
#                       PROFILIM
# ============================================================
@dp.callback_query(F.data == "my_profile")
async def my_profile(callback: types.CallbackQuery):
    if not await require_subscription(callback):
        return
    profile = db_get_profile(callback.from_user.id)
    if not profile or not profile['name']:
        await callback.answer("Sizda hali profil yo'q. Avval profil yarating.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="register")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data="delete_profile")],
        [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")],
    ])
    caption = (f"👤 Ism: {profile['name']}\n🎂 Yosh: {profile['age']}\n"
               f"⚧ Jins: {profile['gender']}\n📍 Shahar: {profile['city']}")
    await callback.message.answer_photo(photo=profile['photo_id'], caption=caption, reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data == "delete_profile")
async def delete_profile(callback: types.CallbackQuery):
    db_delete_profile(callback.from_user.id)
    await callback.message.answer("🗑 Profilingiz o'chirildi.", reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


# ============================================================
#              RANDOM TANISHUV (Like / Mutual Match)
# ============================================================
@dp.callback_query(F.data == "random")
async def random_user(callback: types.CallbackQuery):
    if not await require_subscription(callback):
        return
    my_profile_row = db_get_profile(callback.from_user.id)
    if not my_profile_row or not my_profile_row['name']:
        await callback.answer("Avval profilingizni yarating!", show_alert=True)
        return

    # HOZIRCHA: hamma bir-biriga random ko'rinadi (jins bo'yicha filtr yo'q).
    # Jins bo'yicha filtrlash (faqat qarama-qarshi jins chiqishi) keyinchalik
    # VIP/pullik funksiya sifatida qo'shiladi — o'shanda quyidagi qatorni
    # db_random_profile(callback.from_user.id, opposite_gender) ga almashtiring.
    user = db_random_profile(callback.from_user.id)
    if not user:
        await callback.answer("Hozircha boshqa foydalanuvchilar yo'q.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{user['user_id']}")],
        [InlineKeyboardButton(text="🔄 Keyingisi", callback_data="random")],
        [InlineKeyboardButton(text="🔙 Menyuga qaytish", callback_data="back_to_menu")]
    ])

    caption = (f"👤 Ism: {user['name']}\n🎂 Yosh: {user['age']}\n"
               f"⚧ Jins: {user['gender']}\n📍 Shahar: {user['city']}")

    await callback.message.answer_photo(photo=user['photo_id'], caption=caption, reply_markup=kb)
    await callback.answer()


@dp.callback_query(F.data.startswith("like_"))
async def process_like(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[1])

    if target_id == callback.from_user.id:
        await callback.answer("O'zingizni like qila olmaysiz 🙂", show_alert=True)
        return

    is_match = db_add_like(callback.from_user.id, target_id)

    # Layk bosilgan zahoti o'sha odamning username'ini ko'rsatamiz
    try:
        target_chat = await bot.get_chat(target_id)
        target_username = target_chat.username
    except (TelegramForbiddenError, TelegramBadRequest):
        target_profile = db_get_profile(target_id)
        target_username = target_profile['username'] if target_profile else None

    target_link = f"@{target_username}" if target_username else "username yashirin (profilida username yo'q)"
    await callback.message.answer(f"❤️ Like yuborildi!\n👤 Bog'lanish uchun: {target_link}")

    if is_match:
        my_username = callback.from_user.username
        my_link = f"@{my_username}" if my_username else "username yashirin"
        await callback.message.answer("🎉 <b>Bu — MATCH!</b>\nBir-biringizga yoqib qoldingiz.",
                                       parse_mode="HTML")
        try:
            await bot.send_message(target_id, f"🎉 <b>Sizga MATCH bor!</b>\n👤 Bog'lanish uchun: {my_link}",
                                    parse_mode="HTML")
        except (TelegramForbiddenError, TelegramBadRequest):
            pass

    await callback.answer()


# ============================================================
#                       ADMIN PANEL
# ============================================================
@dp.callback_query(F.data == "admin")
async def admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Sizda ruxsat yo'q.", show_alert=True)
        return
    await callback.message.edit_text("⚙️ <b>Admin Panel</b>", parse_mode="HTML", reply_markup=admin_kb())
    await callback.answer()


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    s = db_stats()
    text = (f"📊 <b>Statistika</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{s['total']}</b>\n"
            f"🆕 Bugun qo'shilganlar: <b>{s['today']}</b>\n"
            f"❤️ Jami like'lar: <b>{s['likes']}</b>\n"
            f"⛔ Bloklangan: <b>{s['banned']}</b>")
    await callback.message.answer(text, parse_mode="HTML", reply_markup=admin_kb())
    await callback.answer()


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yozing "
                                   "(matn, rasm yoki video bo'lishi mumkin):")
    await state.set_state(AdminState.broadcast)
    await callback.answer()


@dp.message(AdminState.broadcast)
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    await state.clear()
    user_ids = db_all_user_ids()
    sent, failed = 0, 0
    status_msg = await message.answer(f"⏳ Yuborilmoqda... 0/{len(user_ids)}")

    for i, uid in enumerate(user_ids, start=1):
        try:
            await message.copy_to(chat_id=uid)
            sent += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        await asyncio.sleep(0.05)  # flood limitdan saqlanish uchun
        if i % 25 == 0:
            try:
                await status_msg.edit_text(f"⏳ Yuborilmoqda... {i}/{len(user_ids)}")
            except TelegramBadRequest:
                pass

    await status_msg.edit_text(f"✅ Yuborish yakunlandi!\n📤 Yuborildi: {sent}\n❌ Xato: {failed}")
    await message.answer("⚙️ Admin Panel", reply_markup=admin_kb())


@dp.callback_query(F.data == "admin_ban")
async def admin_ban_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("⛔ Bloklamoqchi bo'lgan foydalanuvchining ID raqamini yuboring:")
    await state.set_state(AdminState.ban_user)
    await callback.answer()


@dp.message(AdminState.ban_user)
async def admin_ban_process(message: types.Message, state: FSMContext):
    await state.clear()
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Noto'g'ri ID. Qayta urinib ko'ring.", reply_markup=admin_kb())
        return
    db_set_ban(int(message.text), True)
    await message.answer(f"✅ Foydalanuvchi {message.text} bloklandi.", reply_markup=admin_kb())


@dp.callback_query(F.data == "admin_unban")
async def admin_unban_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer("✅ Blokdan chiqarmoqchi bo'lgan foydalanuvchining ID raqamini yuboring:")
    await state.set_state(AdminState.unban_user)
    await callback.answer()


@dp.message(AdminState.unban_user)
async def admin_unban_process(message: types.Message, state: FSMContext):
    await state.clear()
    if not message.text or not message.text.isdigit():
        await message.answer("❌ Noto'g'ri ID. Qayta urinib ko'ring.", reply_markup=admin_kb())
        return
    db_set_ban(int(message.text), False)
    await message.answer(f"✅ Foydalanuvchi {message.text} blokdan chiqarildi.", reply_markup=admin_kb())


# ============================================================
#                    BLOKLANGANLARNI TO'SISH
# ============================================================
@dp.message()
async def block_banned_fallback(message: types.Message, state: FSMContext):
    """FSM holatida bo'lmagan va boshqa hech qanday handlerga tushmagan xabarlar uchun."""
    profile = db_get_profile(message.from_user.id)
    if profile and profile['is_banned']:
        await message.answer("⛔ Siz botdan foydalanish huquqidan mahrum qilingansiz.")
        return
    if not await require_subscription(message):
        return
    await message.answer("Quyidagi menyudan foydalaning:", reply_markup=get_main_kb(message.from_user.id))


# ============================================================
#                          ISHGA TUSHIRISH
# ============================================================
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
