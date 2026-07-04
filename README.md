# Tanishuv Bot PRO — O'rnatish va Xavfsizlik Qo'llanmasi

## ⚠️ 1-QADAM — Eski tokenni hoziroq bekor qiling

Sizning eski tokeningiz chatda oshkor bo'lgan edi. Agar hali qilmagan bo'lsangiz:

1. Telegram'da **@BotFather** ga o'ting
2. `/mybots` → botingizni tanlang
3. **API Token** → **Revoke current token**
4. Yangi tokenni **hech kimga, hech qayerga (chat, GitHub, forum) yubormang**

## 2-QADAM — Railway'da sozlash

### a) Loyihani yuklash
GitHub repo yarating va shu papkadagi barcha fayllarni yuklang (`.env` faylini EMAS — u faqat lokal uchun, `.gitignore` uni avtomatik chetlab o'tadi).

### b) Environment Variables (Railway → Settings → Variables)

| Nomi | Qiymati | Izoh |
|---|---|---|
| `BOT_TOKEN` | yangi tokeningiz | BotFather'dan olingan yangi token |
| `ADMIN_IDS` | masalan `123456789` | Sizning Telegram user ID'ingiz (bir nechta bo'lsa vergul bilan: `111,222`) |
| `REQUIRED_CHANNEL` | `@kanal_username` | Majburiy obuna kanali (kerak bo'lmasa bo'sh qoldiring) |
| `DB_PATH` | `/data/tanishuv.db` | Quyidagi Volume bilan MOS bo'lishi shart |

O'z Telegram ID'ingizni bilish uchun **@userinfobot** ga `/start` yozing.

### c) Volume qo'shish — MA'LUMOTLAR YO'QOLMASLIGI UCHUN ENG MUHIM QADAM

1. Railway → Service → **Settings** → **Volumes** → **New Volume**
2. Mount path: `/data`
3. Saqlang

Bu bo'lmasa, har safar qayta deploy qilganingizda barcha profillar, like/matchlar o'chib ketadi (Railway konteyneri har deployda "toza" holatga qaytadi). Volume qo'shilgach, `/data` papkasi doimiy saqlanadi.

### d) Start Command
Railway avtomatik aniqlaydi, lekin agar so'rasa:
```
python bot.py
```

## 3-QADAM — Lokal test qilish (ixtiyoriy)

```bash
pip install -r requirements.txt python-dotenv
cp .env.example .env
# .env faylini oching va o'z token/ID'ingizni kiriting
python run_local.py
```

## 🔐 Botga kiritilgan xavfsizlik choralari

- **Token kodda emas** — faqat Environment Variable orqali o'qiladi (`config.py`)
- **SQL-injection'dan himoya** — barcha so'rovlar parametrlashtirilgan (`db.py`), hech qayerda foydalanuvchi matni to'g'ridan-to'g'ri SQL ichiga qo'yilmagan
- **Admin whitelist** — faqat `ADMIN_IDS` da ko'rsatilgan Telegram ID'lar admin buyruqlarni ishlatadi; ruxsatsiz urinishlar log'ga yoziladi va jim rad etiladi (buning borligi ham oshkor qilinmaydi)
- **HTML/parse-mode injection'dan himoya** — foydalanuvchi kiritgan ism/bio matnlari boshqalarga ko'rsatishdan oldin `html.escape()` orqali tozalanadi (`security.py`)
- **Flood/spam himoyasi** — har foydalanuvchi uchun ketma-ket amallar orasida minimal kutish vaqti (`FLOOD_LIMIT_SECONDS`)
- **Ban tizimi** — admin xohlagan foydalanuvchini bloklay oladi (`/ban`, `/unban`), banlangan foydalanuvchilar boshqalarga ko'rinmaydi
- **Report tizimi** — foydalanuvchilar bir-birini shikoyat qila oladi, bu ma'lumotlar bazasida saqlanadi
- **Yosh cheklovi** — faqat 18-70 yosh oralig'idagi profillarga ruxsat (`MIN_AGE`/`MAX_AGE`)
- **Webhook konflikti oldini olish** — bot ishga tushganda avtomatik `delete_webhook()` chaqiradi
- **WAL rejimi** — SQLite bir vaqtda ko'p so'rovlarni xavfsiz qayta ishlaydi

## ⚠️ Yana bilishingiz kerak bo'lgan narsalar

- Bu himoya choralari botni **ancha xavfsizroq** qiladi, lekin "100% buzib bo'lmaydigan" tizim mavjud emas — bu hech qanday dasturiy ta'minotga tegishli emas. Eng katta xavf odatda texnik zaiflik emas, balki **tokenning tasodifan oshkor bo'lishi** (chatda, GitHub'da, skrinshotda). Shuning uchun yuqoridagi qoidalarga doim rioya qiling.
- Agar kelajakda token yana oshkor bo'lib qolsa — darhol BotFather orqali revoke qiling, bu eng tez va ishonchli himoya.
- Admin ID'ingizni hech kimga aytmang — bu sizning admin buyruqlaringizni ishlatishga urinishlarning oldini olishga yordam beradi.
