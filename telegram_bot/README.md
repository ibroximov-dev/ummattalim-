# Bilim aniqlash boti

## ⚠️ Xavfsizlik — birinchi navbatda shuni qiling
Agar tokeningizni biror joyda (chat, GitHub va h.k.) oshkor qilgan bo'lsangiz,
**@BotFather** ga kiring → `/mybots` → botingiz → **API Token** → **Revoke**,
va yangi token oling. Eski oshkor bo'lgan token bilan ishlamang.

Tokenni koddagi hech bir faylga yozmang — `.env` fayl orqali bering (pastga qarang).

## O'rnatish

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Sozlash

Loyiha papkasida `.env.example` faylining nusxasini oling va nomini **`.env`**
qiling (aynan shu nom bilan, `.example` qismisiz), so'ng ichiga yozing:

```
BOT_TOKEN=BotFather_dan_olgan_tokeningiz
ADMIN_IDS=sizning_telegram_id_raqamingiz
```

Telegram ID'ingizni `@userinfobot` orqali bilib olishingiz mumkin. Bir nechta
admin bo'lsa, ID'larni vergul bilan ajrating: `ADMIN_IDS=111,222`.

## Ishga tushirish

```bash
python3 main.py
```

Bot ishga tushgach, Telegram'da botga `/start` yuboring.

## Foydalanuvchi oqimi

1. `/start` — agar foydalanuvchi birinchi marta kirsa, kontakt so'raladi.
2. Kontakt yuborilgach — ism so'raladi.
3. Ism kiritilgach — mavjud fanlar ro'yxati (tugmalar) chiqadi.
4. Fan tanlanadi → savollar birma-bir tugmali variantlar bilan chiqadi.
5. Test tugagach — necha foiz to'g'ri javob berilgani va daraja ko'rsatiladi.

**Muhim:** foydalanuvchi bazada saqlangan bo'lsa (kontakt + ism bor),
keyingi safar `/start` bosganda kontakt **qayta so'ralmaydi** — to'g'ridan-to'g'ri
fan tanlashga o'tadi.

### Daraja hisoblash mantig'i
- 0 yoki 1 ta to'g'ri javob → 🔴 Boshlang'ich daraja (0-darajadan)
- 50% dan kam (lekin 2+ to'g'ri) → 🟠 O'rtachadan past
- 50%–79% → 🟡 O'rtacha daraja
- 80% va undan yuqori → 🟢 Yuqori daraja

Bu chegaralarni `handlers/user.py` faylidagi `daraja_aniqlash()` funksiyasida
xohlaganingizcha o'zgartirishingiz mumkin.

## Admin buyruqlari

Faqat `ADMIN_IDS` ro'yxatidagi Telegram ID'lar bu buyruqlarni ishlata oladi
(username kerak emas). To'liq yordam uchun botga `/admin_help` yozing.

### 1. Fan qo'shish
```
/fan IT
```
Bot javobi: `✅ Qo'shildi: IT`

### 2. Fanni o'chirish (barcha savollari bilan)
```
/fan del IT
```
Bot javobi: `❌ O'chirildi: IT`

### 3. Fan nomini tahrirlash
```
/fan edit IT Informatika
```
Bot javobi: `⚠️ Tahrirlandi: IT → Informatika` (bu fanga tegishli barcha
savollar ham avtomatik yangi nomga ko'chadi)

### 4. Savol qo'shish / tahrirlash
```
/fan_savol IT 1) print nima vazifa bajaradi.
A) hichnarsa qimedi
B) oqiydi
C) Natija qaytaradi
+D) ozgaruvchidan qiymatni olib beradi
```
To'g'ri javob oldiga **+** qo'yiladi. Bot javobi: `✅ Qo'shildi IT 1)`

Xuddi shu raqam (`1)`) bilan qayta yuborsangiz — savol yangilanadi:
`⚠️ Tahrirlandi IT 1)`

### 5. Savolni o'chirish
```
/fan_savol IT del 1)
```
Bot javobi: `❌ O'chirildi IT 1)`

## Men qabul qilgan taxminlar (assumptions)

1. **Fan nomi bir so'zdan iborat** (masalan `IT`, `Matematika`) — orasida
   bo'sh joy bo'lmasligi kerak.
2. **`/fan edit`** ikkita argument talab qiladi (eski nom va yangi nom),
   chunki faqat bitta nom bilan tahrirlaydigan hech narsa yo'q.
3. **"Savol tahrirlash" alohida buyruq emas** — xuddi shu fan+raqam bilan
   savolni qayta yuborish uni tahrirlaydi (upsert).
4. Savolda kamida 2 ta variant va albatta bitta **+** belgili to'g'ri javob
   bo'lishi shart, aks holda bot xatolik haqida yozadi.
5. `/fan_savol` bilan savol qo'shishdan oldin fan `/fan` orqali oldindan
   qo'shilgan bo'lishi kerak — bo'lmasa bot shuni eslatadi.

## Fayllar tuzilishi
```
telegram_bot/
├── main.py            # botni ishga tushirish
├── config.py           # token, admin ID'lar (.env dan o'qiydi)
├── database.py          # SQLite bilan ishlash (async)
├── states.py            # FSM holatlari
├── handlers/
│   ├── user.py           # /start, kontakt, ism, test
│   └── admin.py          # /fan, /fan_savol, /admin_help
├── .env.example          # nusxa olib .env qiling
└── requirements.txt
```
