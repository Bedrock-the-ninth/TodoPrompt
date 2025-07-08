import sqlite3

def execute_query(query, params=(), fetch=False):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor
        cursor.execute(query, params)
        return cursor.fetchall() if fetch else None
    

def db_initiator():
    execute_query('''CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER UNIQUE PRIMARY KEY, timezone TEXT, reminder_done_enabled BOOLEAN, reminder_left_enabled BOOLEAN);\
                  CREATE TABLE IF NOT EXISTS tasks(id INTEGER UNIQUE PRIMARY KEY, user_id INTEGER, content TEXT, priority INTEGER, is_done BOOLEAN, create_at TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(telegram_id));\
                  CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id);
                  ''')
    

def is_a_user(tid: str):
    user = str(execute_query("SELECT * FROM users WHERE telegram_id = ?", params=(tid,), fetch=True))

    if user[0]:
        return True
    else:
        return False


def validate_timezone(user_input):
    pass

def create_user_profile(tid, tz):
    pass