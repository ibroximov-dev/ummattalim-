from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext

from states import Reg, Quiz
import database as db

router = Router()


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def fanlar_keyboard():
    fanlar = await db.list_fanlar()
    if not fanlar:
        return None
    rows = [[InlineKeyboardButton(text=f, callback_data=f"fan:{f}")] for f in fanlar]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)

    # Agar foydalanuvchi avval ro'yxatdan o'tgan bo'lsa (kontakt + ism bor),
    # /start bosganda qayta kontakt so'ralmaydi — to'g'ridan-to'g'ri fan tanlashga o'tadi.
    if user and user["phone"] and user["full_name"]:
        kb = await fanlar_keyboard()
        if kb is None:
            await message.answer("Hozircha hech qanday fan qo'shilmagan. Keyinroq urinib ko'ring.")
            return
        await message.answer(
            f"Xush kelibsiz, {user['full_name']}! Qaysi fan bo'yicha bilimingizni aniqlamoqchisiz?",
            reply_markup=kb,
        )
        return

    # Telefon raqami avval saqlangan, lekin ism hali kiritilmagan bo'lsa
    # (masalan bot qayta ishga tushirilib, holat yo'qolgan bo'lsa) —
    # kontaktni qayta so'ramasdan, to'g'ridan-to'g'ri ismni so'raymiz.
    if user and user["phone"]:
        await message.answer(
            "Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Reg.waiting_name)
        return

    await message.answer(
        "Assalomu alaykum! Botdan foydalanish uchun avval kontaktingizni yuboring 👇",
        reply_markup=contact_keyboard(),
    )
    await state.set_state(Reg.waiting_contact)


@router.message(Reg.waiting_contact, F.contact)
async def got_contact(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer("Iltimos, aynan o'zingizning kontaktingizni yuboring.")
        return
    await db.save_user_phone(message.from_user.id, message.contact.phone_number)
    await message.answer("Rahmat! Endi ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Reg.waiting_name)


@router.message(Reg.waiting_contact)
async def contact_required(message: Message):
    await message.answer("Iltimos, pastdagi tugma orqali kontaktingizni yuboring 👇")


@router.message(Reg.waiting_name, F.text)
async def got_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    await db.save_user_name(message.from_user.id, full_name)
    await state.clear()

    kb = await fanlar_keyboard()
    if kb is None:
        await message.answer(f"Rahmat, {full_name}! Hozircha hech qanday fan qo'shilmagan.")
        return

    await message.answer(
        f"Rahmat, {full_name}! Qaysi fan bo'yicha bilimingizni aniqlamoqchisiz?",
        reply_markup=kb,
    )


def question_keyboard(q_index: int, options: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=opt, callback_data=f"ans:{q_index}:{i}")]
        for i, opt in enumerate(options)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def send_question(target, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    q = questions[index]
    text = f"{index + 1}/{len(questions)}-savol:\n\n{q['question']}"
    kb = question_keyboard(index, q["options"])
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("fan:"))
async def choose_fan(callback: CallbackQuery, state: FSMContext):
    fan = callback.data.split(":", 1)[1]
    questions = await db.get_questions(fan)
    if not questions:
        await callback.answer()
        await callback.message.answer(f"'{fan}' fani bo'yicha hali savollar qo'shilmagan.")
        return

    await state.set_state(Quiz.in_progress)
    await state.update_data(fan=fan, questions=questions, index=0, score=0)
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await send_question(callback, state)


def daraja_aniqlash(score: int, total: int) -> str:
    if total == 0:
        return "Noma'lum"
    percent = score / total * 100
    # 0 yoki 1 ta to'g'ri javob — eng boshidan (0-darajadan) boshlanadi
    if score <= 1:
        return "🔴 Boshlang'ich daraja (0-darajadan boshlanadi)"
    if percent < 50:
        return "🟠 O'rtachadan past daraja"
    if percent < 80:
        return "🟡 O'rtacha daraja"
    return "🟢 Yuqori daraja"


@router.callback_query(Quiz.in_progress, F.data.startswith("ans:"))
async def answer_question(callback: CallbackQuery, state: FSMContext):
    _, q_index_str, opt_index_str = callback.data.split(":")
    q_index = int(q_index_str)
    opt_index = int(opt_index_str)

    data = await state.get_data()
    questions = data["questions"]
    index = data["index"]
    score = data["score"]

    if q_index != index:
        await callback.answer("Bu savolga allaqachon javob berilgan.", show_alert=True)
        return

    correct = questions[index]["correct_index"]
    is_correct = opt_index == correct
    if is_correct:
        score += 1

    await callback.answer("✅ To'g'ri!" if is_correct else "❌ Noto'g'ri")
    await callback.message.edit_reply_markup(reply_markup=None)

    index += 1
    if index >= len(questions):
        total = len(questions)
        percent = round(score / total * 100)
        daraja = daraja_aniqlash(score, total)
        await callback.message.answer(
            f"Test yakunlandi! 🎉\n\n"
            f"Fan: {data['fan']}\n"
            f"Natija: {score}/{total} ({percent}%)\n\n"
            f"Daraja: {daraja}"
        )
        await state.clear()
        return

    await state.update_data(index=index, score=score)
    await send_question(callback, state)
