import sqlite3
import pytz
from datetime import datetime, timezone, timedelta

FORMAT_STRING = "%Y-%m-%d %H:%M:%S"


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


def get_offset(string_offset: str) -> timedelta:
    if string_offset[3] == "+":
        offset_hours = int(string_offset[4:6])
    else:
        offset_hours = -int(string_offset[4:6])
    offset_minutes = int(string_offset[7:])

    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    return offset


def get_user_local_time(tid: int) -> datetime:
    string_offset = (execute_query("SELECT timezone FROM users WHERE telegram_id = ?", (tid,), True))[0]

    offset = get_offset(string_offset)
    current_utc_time = datetime.now(timezone.utc)

    user_local_time = current_utc_time + offset

    return user_local_time


def add_user_tasks(tid: int, task: str, priority: int) -> int:
    user_current_time_string = datetime.strftime(get_user_local_time(tid), FORMAT_STRING)

    if priority in [1, 2, 3]:
        try:
            execute_query("INSERT INTO tasks (user_id, content, priority, created_at) VALUES (?, ?, ?, ?)",
                           params=(tid, task, priority, user_current_time_string))
        except sqlite3.Error:
            return 2
        else:
            execute_query("UPDATE users SET reminder_left_enabled = TRUE")
    else:
        return 1


def get_user_tasks(tid):
    
    date = datetime.strftime(get_user_local_time(tid), "%Y-%m-%d") + "%"
    query = (
        "SELECT * FROM tasks "
        "WHERE (user_id = ? AND (created_at LIKE ?)) "
        "ORDER BY priority ASC,created_at ASC "
    )

    try:
        today_tasks = execute_query(query, (tid, date), True)
    except sqlite3.Error:
        return 1
    else:
        return today_tasks


def format_tasks(task_list):
    pass