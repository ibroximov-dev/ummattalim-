import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import database as db
from config import ADMIN_IDS

router = Router()


def is_admin(message: Message) -> bool:
    return message.from_user.id in ADMIN_IDS


ADMIN_HELP_TEXT = (
    "🛠 <b>Admin buyruqlari</b>\n\n"
    "1️⃣ <b>Fan qo'shish</b>\n"
    "<code>/fan IT</code>\n\n"
    "2️⃣ <b>Fanni o'chirish</b> (ichidagi barcha savollari bilan)\n"
    "<code>/fan del IT</code>\n\n"
    "3️⃣ <b>Fan nomini tahrirlash</b>\n"
    "<code>/fan edit ESKI_NOM YANGI_NOM</code>\n"
    "Masalan: <code>/fan edit IT Informatika</code>\n\n"
    "4️⃣ <b>Savol qo'shish / tahrirlash</b>\n"
    "<code>/fan_savol IT 1) Savol matni\n"
    "A) variant\n"
    "B) variant\n"
    "+C) to'g'ri variant\n"
    "D) variant</code>\n"
    "To'g'ri javob oldiga <b>+</b> belgisi qo'yiladi (foydalanuvchiga bu belgi ko'rinmaydi).\n"
    "Agar shu N) raqamli savol allaqachon mavjud bo'lsa — u tahrirlanadi (qayta yoziladi).\n\n"
    "5️⃣ <b>Savolni o'chirish</b>\n"
    "<code>/fan_savol IT del 1)</code>\n\n"
    "ℹ️ Har bir amaldan so'ng bot natijani belgi bilan tasdiqlaydi:\n"
    "✅ qo'shildi   ⚠️ tahrirlandi   ❌ o'chirildi"
)


@router.message(Command("admin_help"))
async def admin_help(message: Message):
    if not is_admin(message):
        return
    await message.answer(ADMIN_HELP_TEXT)


@router.message(Command("fan"))
async def cmd_fan(message: Message):
    if not is_admin(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Foydalanish: /fan NOM  yoki  /fan del NOM  yoki  /fan edit ESKI YANGI")
        return
    body = args[1].strip()
    parts = body.split()

    # /fan del NOM
    if parts[0] == "del":
        if len(parts) != 2:
            await message.answer("Foydalanish: /fan del NOM")
            return
        fan = parts[1]
        if not await db.fan_exists(fan):
            await message.answer(f"'{fan}' nomli fan topilmadi.")
            return
        await db.delete_fan(fan)
        await message.answer(f"❌ O'chirildi: {fan}")
        return

    # /fan edit ESKI YANGI
    if parts[0] == "edit":
        if len(parts) != 3:
            await message.answer("Foydalanish: /fan edit ESKI_NOM YANGI_NOM")
            return
        old_name, new_name = parts[1], parts[2]
        if not await db.fan_exists(old_name):
            await message.answer(f"'{old_name}' nomli fan topilmadi.")
            return
        await db.rename_fan(old_name, new_name)
        await message.answer(f"⚠️ Tahrirlandi: {old_name} → {new_name}")
        return

    # /fan NOM  -> qo'shish
    if len(parts) != 1:
        await message.answer("Foydalanish: /fan NOM  (fan nomida bo'sh joy bo'lmasin)")
        return
    fan = parts[0]
    is_new = await db.add_fan(fan)
    if is_new:
        await message.answer(f"✅ Qo'shildi: {fan}")
    else:
        await message.answer(f"'{fan}' fani allaqachon mavjud.")


@router.message(Command("fan_savol"))
async def cmd_fan_savol(message: Message):
    if not is_admin(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Foydalanish uchun /admin_help ga qarang.")
        return
    body = args[1].strip()

    m = re.match(r"^(\S+)\s+(.*)$", body, re.S)
    if not m:
        await message.answer("Foydalanish uchun /admin_help ga qarang.")
        return
    fan, rest = m.groups()
    rest = rest.strip()

    if not await db.fan_exists(fan):
        await message.answer(f"'{fan}' nomli fan topilmadi. Avval /fan {fan} bilan qo'shing.")
        return

    if rest.startswith("del "):
        numpart = rest[4:].strip()
        num_m = re.match(r"^(\d+)\)?", numpart)
        if not num_m:
            await message.answer("Foydalanish: /fan_savol FAN del N)")
            return
        number = int(num_m.group(1))
        await db.delete_question(fan, number)
        await message.answer(f"❌ O'chirildi {fan} {number})")
        return

    q_m = re.match(r"^(\d+)\)\s*(.*)$", rest, re.S)
    if not q_m:
        await message.answer("Foydalanish uchun /admin_help ga qarang.")
        return
    number = int(q_m.group(1))
    body_text = q_m.group(2)
    lines = [l for l in body_text.split("\n") if l.strip()]
    if len(lines) < 3:
        await message.answer("Savol matni va kamida 2 ta variant kerak.")
        return

    question_text = lines[0].strip()
    options = []
    correct_index = None
    for line in lines[1:]:
        line = line.strip()
        is_correct = line.startswith("+")
        if is_correct:
            line = line[1:].strip()
        opt_m = re.match(r"^[A-Za-z]\)\s*(.*)$", line)
        opt_text = opt_m.group(1).strip() if opt_m else line
        if is_correct:
            correct_index = len(options)
        options.append(opt_text)

    if correct_index is None:
        await message.answer("To'g'ri javob belgilanmagan. To'g'ri variant oldiga + qo'ying (masalan: +D).")
        return

    existed = await db.question_exists(fan, number)
    await db.upsert_question(fan, number, question_text, options, correct_index)

    if existed:
        await message.answer(f"⚠️ Tahrirlandi {fan} {number})")
    else:
        await message.answer(f"✅ Qo'shildi {fan} {number})")
