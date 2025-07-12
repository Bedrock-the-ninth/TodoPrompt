import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
DATABASE_NAME = DATA_DIR / "database.db"


def execute_query(query, params=(), fetch=False):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            fetched = cursor.fetchall()
            if len(fetched) > 0:
                return fetched
            else:
                return None
        else:
            conn.commit()
            return None

def db_initiator():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users(
                telegram_id INTEGER UNIQUE PRIMARY KEY,
                timezone TEXT,
                reminder_done_enabled BOOLEAN DEFAULT FALSE,
                reminder_left_enabled BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                content TEXT,
                priority INTEGER CHECK (priority IN (1, 2, 3)), 
                is_done BOOLEAN DEFAULT FALSE, 
                created_at TIMESTAMP, 
                FOREIGN KEY (user_id) REFERENCES users(telegram_id));
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER,
                type TEXT CHECK (type IN ('DONE', 'LEFT')),
                reminder_time_locale TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );
            CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id);
        ''')