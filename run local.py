# run_local.py
# Faqat LOKAL kompyuterda test qilish uchun (.env faylini o'qib beradi).
# Railway'da bu fayl kerak emas — Railway to'g'ridan-to'g'ri "python bot.py" ni ishlatadi
# va Environment Variable'larni o'zi yuklaydi.

from dotenv import load_dotenv
load_dotenv()

import asyncio
from bot import main

if __name__ == "__main__":
    asyncio.run(main())
