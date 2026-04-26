import aiosqlite

DB_NAME = "bot.db"


async def init_db():
    db = await aiosqlite.connect(DB_NAME)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'ru',
            level INTEGER DEFAULT 0,
            last_check_date TEXT DEFAULT ''
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS enemies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            main_pic TEXT,
            task_text TEXT,
            task_date INTEGER,
            created_date TEXT,
            done INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    await db.commit()
    await db.close()
    print("База данных инициализирована")


async def get_db():
    return await aiosqlite.connect(DB_NAME)