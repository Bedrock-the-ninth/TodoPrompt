import sqlite3
import pytz
import datetime
from datetime import datetime

def execute_query(query, params=(), fetch=False):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return None 
    

def db_initiator():
    with sqlite3.connect("database.db") as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users(
                telegram_id INTEGER UNIQUE PRIMARY KEY,
                timezone TEXT,
                reminder_done_enabled BOOLEAN,
                reminder_left_enabled BOOLEAN
            );
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER UNIQUE PRIMARY KEY,
                user_id INTEGER,
                content TEXT,
                priority INTEGER,
                is_done BOOLEAN,
                create_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );
            CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id);
        ''')
    

def is_a_user(tid: str):
    user = execute_query('SELECT * FROM users WHERE telegram_id = ?', params=(tid,), fetch=True)

    if len(user) > 0:
        return True
    else:
        return False

def is_timezone_valid(user_input: str) -> bool:
    return (user_input in pytz.all_timezones_set)

def create_user_profile(tid, user_input):
    user_tz = pytz.timezone(user_input)
    user_tz_raw = datetime.now(user_tz).strftime("%z")
    user_tz_offset = f"UTC{user_tz_raw[0:3]}:{user_tz_raw[3:]}"

    execute_query(query="INSERT INTO users VALUES (?, ?, ?, ?)", params=(tid, user_tz_offset, False, False))