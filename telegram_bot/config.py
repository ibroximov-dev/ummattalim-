import os
from dotenv import load_dotenv

# Loyiha papkasidagi .env faylini o'qiydi (BOT_TOKEN, ADMIN_IDS shu yerdan olinadi)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
]

DB_PATH = os.getenv("DB_PATH", "bot.db")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi! Loyiha papkasida .env fayl yarating va ichiga "
        'BOT_TOKEN="..." qatorini yozing (.env.example faylga qarang).'
    )
