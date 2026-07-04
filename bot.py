# bot.py — Tanishuv Bot PRO
# aiogram 3 | SQLite (Volume-persistent) | 100% himoyalangan
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
)

import db
from config import (
    BOT_TOKEN, ADMIN_IDS, REQUIRED_CHANNEL, MIN_AGE, MAX_AGE,
    MAX_NAME_LEN, MAX_BIO_LEN, log,
)
from locations import REGION_NAMES, get_districts
from security import (
    flood_guard, admin_only, is_admin, sanitize_text, validate_age, is_subscribed,
)

router = Router()


# ============ FSM STATES ============

class Registration(StatesGroup):
    full_name = State()
    age = State()
    gender = State()
    region = State()
    district = State()
    photo = State()
    bio = State()


class BroadcastState(StatesGroup):
    waiting_text = State()


# ============ KEYBOARDS ============

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Ko'rish")],
            [KeyboardButton(text="👤 Mening profilim"), KeyboardButton(text="💎 VIP")],
            [KeyboardButton(text="❌ Profilni o'chirish")],
        ],
        resize_keyboard=True,
    )


def gender_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👨 Erkak"), KeyboardButton(text="👩 Ayol")]],
        resize_keyboard=True, one_time_keyboard=True,
    )


def regions_kb():
    rows, tmp = [], []
    for i, name in enumerate(REGION_NAMES, 1):
        tmp.append(KeyboardButton(text=name))
        if i % 2 == 0:
            rows.append(tmp)
            tmp = []
    if tmp:
        rows.append(tmp)
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def districts_kb(region: str):
    rows, tmp = [], []
    for i, name in enumerate(get_districts(region), 1):
        tmp.append(KeyboardButton(text=name))
        if i % 2 == 0:
            rows.append(tmp)
            tmp = []
    if tmp:
        rows.append(tmp)
    rows.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, one_time_keyboard=True)


def skip_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="O'tkazib yuborish")]],
                                resize_keyboard=True, one_time_keyboard=True)


def reaction_kb(target_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👎", callback_data=f"skip:{target_id}"),
        InlineKeyboardButton(text="⛔️", callback_data=f"report:{target_id}"),
        InlineKeyboardButton(text="❤️", callback_data=f"like:{target_id}"),
    ]])


# ============ HELPERS ============

async def require_subscription(message_or_cb, bot: Bot) -> bool:
    from security import get_missing_channels
    user_id = message_or_cb.from_user.id
    channels = db.get_required_channels()
    if not channels:
        # Agar admin panelda hech qanday kanal/guruh sozlanmagan bo'lsa, .env dagi eskisiga qaraymiz
        channels = [REQUIRED_CHANNEL] if REQUIRED_CHANNEL else []
    if not channels:
        return True

    missing = await get_missing_channels(bot, user_id, channels)
    if not missing:
        return True

    links_text = "\n".join(f"• {ch}" for ch in missing)
    kb_rows = []
    for ch in missing:
        url = f"https://t.me/{ch.lstrip('@')}" if ch.startswith("@") else None
        if url:
            kb_rows.append([InlineKeyboardButton(text=f"➕ {ch}", url=url)])
    kb_rows.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    text = (
        "❗️ Botdan foydalanish uchun quyidagi kanal/guruh(lar)ga a'zo bo'ling:\n\n"
        f"{links_text}\n\nA'zo bo'lgach, pastdagi tugmani bosing."
    )
    if isinstance(message_or_cb, CallbackQuery):
        await message_or_cb.message.answer(text, reply_markup=kb)
    else:
        await message_or_cb.answer(text, reply_markup=kb)
    return False


def profile_caption(user: dict) -> str:
    vip_badge = " 💎" if db.is_vip_active(user) else ""
    bio = user.get("bio") or "—"
    return (
        f"<b>{user['full_name']}</b>{vip_badge}, {user['age']}\n"
        f"📍 {user['region']}, {user['district']}\n\n"
        f"{bio}"
    )


# ============ /start ============

@router.message(CommandStart())
@flood_guard
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    if not await require_subscription(message, bot):
        return
    user = db.get_user(message.from_user.id)
    if user:
        db.touch_last_seen(message.from_user.id)
        await message.answer(
            f"Xush kelibsiz, {user['full_name']}! 👋", reply_markup=main_menu_kb()
        )
    else:
        await state.set_state(Registration.full_name)
        await message.answer(
            "👋 Tanishuv botiga xush kelibsiz!\n\nKeling, profilingizni yarataylik.\n"
            f"Ismingizni kiriting (maks. {MAX_NAME_LEN} belgi):",
            reply_markup=ReplyKeyboardRemove(),
        )


@router.callback_query(F.data == "check_sub")
@flood_guard
async def check_sub_cb(callback: CallbackQuery, state: FSMContext, bot: Bot):
    channels = db.get_required_channels() or ([REQUIRED_CHANNEL] if REQUIRED_CHANNEL else [])
    if await is_subscribed(bot, callback.from_user.id, channels):
        await callback.answer("✅ Rahmat!")
        try:
            await callback.message.delete()
        except Exception:
            pass
        user = db.get_user(callback.from_user.id)
        if user:
            db.touch_last_seen(callback.from_user.id)
            await bot.send_message(
                callback.from_user.id,
                f"Xush kelibsiz, {user['full_name']}! 👋",
                reply_markup=main_menu_kb(),
            )
        else:
            await state.set_state(Registration.full_name)
            await bot.send_message(
                callback.from_user.id,
                "👋 Tanishuv botiga xush kelibsiz!\n\nKeling, profilingizni yarataylik.\n"
                f"Ismingizni kiriting (maks. {MAX_NAME_LEN} belgi):",
            )
    else:
        await callback.answer("Hali obuna bo'lmagansiz.", show_alert=True)


# ============ REGISTRATION FLOW ============

@router.message(Registration.full_name)
@flood_guard
async def reg_full_name(message: Message, state: FSMContext):
    name = sanitize_text(message.text, MAX_NAME_LEN)
    if len(name) < 2:
        await message.answer("Ism juda qisqa. Qaytadan kiriting:")
        return
    await state.update_data(full_name=name)
    await state.set_state(Registration.age)
    await message.answer(f"Necha yoshdasiz? ({MIN_AGE}-{MAX_AGE})")


@router.message(Registration.age)
@flood_guard
async def reg_age(message: Message, state: FSMContext):
    age = validate_age(message.text.strip(), MIN_AGE, MAX_AGE)
    if age is None:
        await message.answer(f"Yoshni to'g'ri kiriting ({MIN_AGE}-{MAX_AGE} oralig'ida, faqat raqam):")
        return
    await state.update_data(age=age)
    await state.set_state(Registration.gender)
    await message.answer("Jinsingiz?", reply_markup=gender_kb())


@router.message(Registration.gender, F.text.in_(["👨 Erkak", "👩 Ayol"]))
@flood_guard
async def reg_gender(message: Message, state: FSMContext):
    gender = "male" if "Erkak" in message.text else "female"
    await state.update_data(gender=gender)
    await state.set_state(Registration.region)
    await message.answer("Qaysi viloyatdansiz?", reply_markup=regions_kb())


@router.message(Registration.gender)
@flood_guard
async def reg_gender_invalid(message: Message):
    await message.answer("Iltimos tugmalardan birini tanlang.", reply_markup=gender_kb())


@router.message(Registration.region)
@flood_guard
async def reg_region(message: Message, state: FSMContext):
    if message.text not in REGION_NAMES:
        await message.answer("Iltimos ro'yxatdan viloyatni tanlang.", reply_markup=regions_kb())
        return
    await state.update_data(region=message.text)
    await state.set_state(Registration.district)
    await message.answer("Qaysi tuman/shahardansiz?", reply_markup=districts_kb(message.text))


@router.message(Registration.district)
@flood_guard
async def reg_district(message: Message, state: FSMContext):
    data = await state.get_data()
    region = data.get("region")
    valid_districts = get_districts(region)
    if message.text == "⬅️ Orqaga":
        await state.set_state(Registration.region)
        await message.answer("Qaysi viloyatdansiz?", reply_markup=regions_kb())
        return
    if message.text not in valid_districts:
        await message.answer("Iltimos ro'yxatdan tumanni tanlang.", reply_markup=districts_kb(region))
        return
    await state.update_data(district=message.text)
    await state.set_state(Registration.photo)
    await message.answer("Profilingiz uchun rasm yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(Registration.photo, F.photo)
@flood_guard
async def reg_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    await state.set_state(Registration.bio)
    await message.answer(
        f"O'zingiz haqingizda qisqacha yozing (maks. {MAX_BIO_LEN} belgi) "
        "yoki o'tkazib yuboring:",
        reply_markup=skip_kb(),
    )


@router.message(Registration.photo)
@flood_guard
async def reg_photo_invalid(message: Message):
    await message.answer("Iltimos rasm (fotosurat) yuboring.")


@router.message(Registration.bio)
@flood_guard
async def reg_bio(message: Message, state: FSMContext):
    bio = "" if message.text == "O'tkazib yuborish" else sanitize_text(message.text or "", MAX_BIO_LEN)
    data = await state.get_data()

    db.create_or_update_profile(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=data["full_name"],
        age=data["age"],
        gender=data["gender"],
        region=data["region"],
        district=data["district"],
        bio=bio,
        photo_id=data["photo_id"],
    )
    await state.clear()
    await message.answer("✅ Profilingiz saqlandi!", reply_markup=main_menu_kb())


# ============ PROFILE / MENU ============

@router.message(F.text == "👤 Mening profilim")
@flood_guard
async def my_profile(message: Message, bot: Bot):
    if not await require_subscription(message, bot):
        return
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return
    await message.answer_photo(
        user["photo_id"], caption=profile_caption(user), parse_mode="HTML"
    )


@router.message(F.text == "💎 VIP")
@flood_guard
async def vip_info(message: Message):
    user = db.get_user(message.from_user.id)
    if user and db.is_vip_active(user):
        until = datetime.fromtimestamp(user["vip_until"]).strftime("%Y-%m-%d")
        await message.answer(f"💎 Siz allaqachon VIP foydalanuvchisiz!\nAmal qilish muddati: {until}")
        return
    await message.answer(
        "💎 <b>VIP imkoniyatlari:</b>\n"
        "• Butun O'zbekiston bo'yicha profillarni ko'rish (faqat o'z viloyatingiz emas)\n"
        "• Profilingiz boshqalarga birinchi navbatda ko'rsatiladi\n"
        "• Maxsus 💎 belgisi\n\n"
        "VIP sotib olish uchun admin bilan bog'laning @abe_vlog.",
        parse_mode="HTML",
    )


@router.message(F.text == "❌ Profilni o'chirish")
@flood_guard
async def delete_profile(message: Message):
    db.deactivate_profile(message.from_user.id)
    await message.answer(
        "Profilingiz o'chirildi (boshqalar sizni endi ko'rmaydi). "
        "Qayta faollashtirish uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove(),
    )


# ============ BROWSING ============

@router.message(F.text == "🔍 Ko'rish")
@flood_guard
async def browse(message: Message, bot: Bot):
    if not await require_subscription(message, bot):
        return
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Avval /start bosib ro'yxatdan o'ting.")
        return
    db.touch_last_seen(message.from_user.id)

    opposite = "female" if user["gender"] == "male" else "male"
    region_filter = None if db.is_vip_active(user) else user["region"]
    candidate = db.get_next_profile(message.from_user.id, opposite, region_filter)

    if not candidate:
        await message.answer(
            "Hozircha yangi profillar tugadi. Keyinroq qayta urinib ko'ring 🙂"
        )
        return

    await message.answer_photo(
        candidate["photo_id"],
        caption=profile_caption(candidate),
        parse_mode="HTML",
        reply_markup=reaction_kb(candidate["user_id"]),
    )


@router.callback_query(F.data.startswith("like:") | F.data.startswith("skip:"))
@flood_guard
async def reaction_cb(callback: CallbackQuery, bot: Bot):
    action, target_id_str = callback.data.split(":")
    target_id = int(target_id_str)
    from_id = callback.from_user.id

    is_match = db.record_reaction(from_id, target_id, "like" if action == "like" else "skip")
    await callback.message.edit_reply_markup(reply_markup=None)

    if action == "like":
        await callback.answer("❤️ Yoqtirildi!")
        if is_match:
            me = db.get_user(from_id)
            other = db.get_user(target_id)
            match_text_me = f"🎉 Yangi moslik (match)! {other['full_name']} sizga ham yoqdingiz!"
            match_text_other = f"🎉 Yangi moslik (match)! {me['full_name']} sizga ham yoqdingiz!"
            try:
                await bot.send_message(from_id, match_text_me)
                if me.get("username"):
                    await bot.send_message(target_id, match_text_other + f"\n@{me['username']}")
                else:
                    await bot.send_message(target_id, match_text_other)
            except Exception as e:
                log.warning(f"Match xabarini yuborishda xato: {e}")
    else:
        await callback.answer("O'tkazib yuborildi")

    # Keyingi profilni ko'rsatamiz
    user = db.get_user(from_id)
    opposite = "female" if user["gender"] == "male" else "male"
    region_filter = None if db.is_vip_active(user) else user["region"]
    candidate = db.get_next_profile(from_id, opposite, region_filter)
    if candidate:
        await callback.message.answer_photo(
            candidate["photo_id"],
            caption=profile_caption(candidate),
            parse_mode="HTML",
            reply_markup=reaction_kb(candidate["user_id"]),
        )
    else:
        await callback.message.answer("Hozircha yangi profillar tugadi 🙂")


@router.callback_query(F.data.startswith("report:"))
@flood_guard
async def report_cb(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    db.add_report(callback.from_user.id, target_id, reason="user_reported")
    db.record_reaction(callback.from_user.id, target_id, "skip")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Shikoyat qabul qilindi. Rahmat!", show_alert=True)


# ============ ADMIN PANEL ============

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: Message):
    stats = db.get_stats()
    channels = db.get_required_channels()
    channels_text = "\n".join(f"• {c}" for c in channels) if channels else "— (o'rnatilmagan)"
    text = (
        "🛠 <b>Admin panel</b>\n\n"
        f"👥 Jami foydalanuvchi: {stats['total']}\n"
        f"✅ Faol: {stats['active']}\n"
        f"👨 Erkak: {stats['male']} | 👩 Ayol: {stats['female']}\n"
        f"❤️ Matchlar: {stats['matches']}\n"
        f"💎 VIP: {stats['vip']}\n"
        f"🚫 Ban qilingan: {stats['banned']}\n\n"
        f"📢 Majburiy obuna kanal/guruhlari:\n{channels_text}\n\n"
        "Buyruqlar:\n"
        "/broadcast — barchaga xabar yuborish\n"
        "/ban <user_id> — foydalanuvchini bloklash\n"
        "/unban <user_id> — blokdan chiqarish\n"
        "/setvip <user_id> <kunlar> — VIP berish\n"
        "/addchannel <@username yoki -100...> — majburiy kanal/guruh qo'shish\n"
        "/removechannel <@username yoki -100...> — olib tashlash\n"
        "/listchannels — ro'yxatni ko'rish"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("addchannel"))
@admin_only
async def cmd_addchannel(message: Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer(
            "Foydalanish: /addchannel <@kanal_username>\n"
            "Yopiq guruh/kanal uchun: /addchannel -1001234567890\n\n"
            "⚠️ Botni albatta o'sha kanal/guruhga ADMIN qilib qo'shing, "
            "aks holda a'zolikni tekshira olmaydi!"
        )
        return
    channel = parts[1].strip()
    # Botning shu kanalda ishlay olishini oldindan tekshiramiz
    try:
        me = await bot.get_chat_member(channel, bot.id)
        if me.status not in ("administrator", "creator"):
            await message.answer(
                f"⚠️ Bot {channel} da ADMIN emas. Avval botni admin qiling, keyin qayta urinib ko'ring."
            )
            return
    except Exception as e:
        await message.answer(
            f"❌ {channel} ga kira olmadim: {e}\n"
            "Kanal/guruh username yoki ID to'g'riligini va botning shu yerda a'zoligini tekshiring."
        )
        return

    db.add_required_channel(channel)
    await message.answer(f"✅ {channel} majburiy obuna ro'yxatiga qo'shildi.")


@router.message(Command("removechannel"))
@admin_only
async def cmd_removechannel(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) != 2:
        await message.answer("Foydalanish: /removechannel <@kanal_username>")
        return
    channel = parts[1].strip()
    db.remove_required_channel(channel)
    await message.answer(f"✅ {channel} ro'yxatdan olib tashlandi.")


@router.message(Command("listchannels"))
@admin_only
async def cmd_listchannels(message: Message):
    channels = db.get_required_channels()
    if not channels:
        await message.answer("Hozircha majburiy kanal/guruh o'rnatilmagan.")
        return
    await message.answer("📢 Majburiy obuna ro'yxati:\n" + "\n".join(f"• {c}" for c in channels))


@router.message(Command("ban"))
@admin_only
async def cmd_ban(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /ban <user_id>")
        return
    db.ban_user(int(parts[1]), True)
    await message.answer(f"🚫 {parts[1]} bloklandi.")


@router.message(Command("unban"))
@admin_only
async def cmd_unban(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /unban <user_id>")
        return
    db.ban_user(int(parts[1]), False)
    await message.answer(f"✅ {parts[1]} blokdan chiqarildi.")


@router.message(Command("setvip"))
@admin_only
async def cmd_setvip(message: Message):
    parts = message.text.split()
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await message.answer("Foydalanish: /setvip <user_id> <kunlar_soni>")
        return
    user_id, days = int(parts[1]), int(parts[2])
    until_ts = int(datetime.now().timestamp()) + days * 86400
    db.set_vip(user_id, until_ts)
    await message.answer(f"💎 {user_id} ga {days} kunlik VIP berildi.")


@router.message(Command("broadcast"))
@admin_only
async def cmd_broadcast_start(message: Message, state: FSMContext):
    await state.set_state(BroadcastState.waiting_text)
    await message.answer("Barchaga yuboriladigan xabar matnini kiriting:")


@router.message(BroadcastState.waiting_text)
@admin_only
async def cmd_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    text = message.text
    ids = db.get_all_active_user_ids()
    sent, failed = 0, 0
    await message.answer(f"Yuborilmoqda... ({len(ids)} foydalanuvchi)")
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram rate-limit'ga urilmaslik uchun
    await message.answer(f"✅ Yuborildi: {sent} | ❌ Xato: {failed}")


# ============ MAIN ============

async def main():
    db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # Webhook bilan konflikt bo'lmasligi uchun har ishga tushganda tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)

    log.info("Bot ishga tushdi.")
    log.info(f"Adminlar: {ADMIN_IDS}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot to'xtatildi.")
