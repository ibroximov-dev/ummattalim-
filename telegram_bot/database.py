import json
import aiosqlite

from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone TEXT,
                full_name TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fanlar (
                name TEXT PRIMARY KEY
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS savollar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fan TEXT NOT NULL,
                number INTEGER NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_index INTEGER NOT NULL,
                UNIQUE(fan, number)
            )
        """)
        await conn.commit()


# ---------------- USERS ----------------

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()


async def save_user_phone(user_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO users (user_id, phone) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone",
            (user_id, phone),
        )
        await conn.commit()


async def save_user_name(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "UPDATE users SET full_name=? WHERE user_id=?", (full_name, user_id)
        )
        await conn.commit()


# ---------------- FANLAR ----------------

async def fan_exists(fan: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT 1 FROM fanlar WHERE name=?", (fan,))
        return await cur.fetchone() is not None


async def add_fan(fan: str) -> bool:
    """Fan qo'shadi. Agar u allaqachon bor bo'lsa False, yangi qo'shilgan bo'lsa True qaytaradi."""
    existed = await fan_exists(fan)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("INSERT OR IGNORE INTO fanlar (name) VALUES (?)", (fan,))
        await conn.commit()
    return not existed


async def delete_fan(fan: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM fanlar WHERE name=?", (fan,))
        await conn.execute("DELETE FROM savollar WHERE fan=?", (fan,))
        await conn.commit()


async def rename_fan(old_name: str, new_name: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("UPDATE fanlar SET name=? WHERE name=?", (new_name, old_name))
        await conn.execute("UPDATE savollar SET fan=? WHERE fan=?", (new_name, old_name))
        await conn.commit()


async def list_fanlar():
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute("SELECT name FROM fanlar ORDER BY name")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


# ---------------- SAVOLLAR ----------------

async def question_exists(fan: str, number: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as conn:
        cur = await conn.execute(
            "SELECT 1 FROM savollar WHERE fan=? AND number=?", (fan, number)
        )
        return await cur.fetchone() is not None


async def upsert_question(fan: str, number: int, question: str, options: list, correct_index: int):
    await add_fan(fan)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            """
            INSERT INTO savollar (fan, number, question, options, correct_index)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fan, number) DO UPDATE SET
                question=excluded.question,
                options=excluded.options,
                correct_index=excluded.correct_index
            """,
            (fan, number, question, json.dumps(options, ensure_ascii=False), correct_index),
        )
        await conn.commit()


async def delete_question(fan: str, number: int):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM savollar WHERE fan=? AND number=?", (fan, number))
        await conn.commit()


async def get_questions(fan: str):
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM savollar WHERE fan=? ORDER BY number", (fan,)
        )
        rows = await cur.fetchall()
        result = []
        for r in rows:
            result.append({
                "number": r["number"],
                "question": r["question"],
                "options": json.loads(r["options"]),
                "correct_index": r["correct_index"],
            })
        return result
