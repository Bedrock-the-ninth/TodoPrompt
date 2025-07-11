import sqlite3
import pytz
from datetime import datetime, timezone, timedelta

FORMAT_STRING_C = "%Y-%m-%d %H:%M:%S"
FORMAT_STRING_DATE = "%Y-%m-%d"
FORMAT_STRING_TIME = "%H:%M:%S"


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
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER,
                type TEXT CHECK (type IN ('DONE', 'LEFT')),
                reminder_time_locale TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );
            CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id);
        ''')
    

def is_a_user(uid: str):
    user = execute_query('SELECT * FROM users WHERE telegram_id = ?', params=(uid,), fetch=True)

    if len(user) > 0:
        return True
    else:
        return False


def is_timezone_valid(user_input: str) -> bool:
    return (user_input in pytz.all_timezones_set)


def create_user_profile(uid, user_input):
    user_tz = pytz.timezone(user_input)
    user_tz_raw = datetime.now(user_tz).strftime("%z")
    user_tz_offset = f"UTC{user_tz_raw[0:3]}:{user_tz_raw[3:]}"

    execute_query(query="INSERT INTO users VALUES (?, ?, ?, ?)", params=(uid, user_tz_offset, False, False))


def get_offset(string_offset: str) -> timedelta:
    if string_offset[3] == "+":
        offset_hours = int(string_offset[4:6])
    else:
        offset_hours = -int(string_offset[4:6])
    offset_minutes = int(string_offset[7:])

    offset = timedelta(hours=offset_hours, minutes=offset_minutes)
    return offset


def get_user_local_time(uid: int) -> datetime:
    string_offset = (execute_query("SELECT timezone FROM users WHERE telegram_id = ?", (uid,), True))[0]

    offset = get_offset(string_offset)
    current_utc_time = datetime.now(timezone.utc)

    user_local_time = current_utc_time + offset

    return user_local_time


def add_user_task(uid: int, task: str, priority: int) -> int:

    user_current_time_string = datetime.strftime(get_user_local_time(uid), FORMAT_STRING_C)

    if priority in [1, 2, 3]:
        try:
            execute_query("INSERT INTO tasks (user_id, content, priority, created_at) VALUES (?, ?, ?, ?)",
                           params=(uid, task, priority, user_current_time_string))
        except sqlite3.Error:
            return 2
        else:
            execute_query("UPDATE users SET reminder_left_enabled = TRUE")
    else:
        return 1





def format_tasks(task_list):
    pass



class User:
    def __init__(self, uid):
        self.uid: int = uid,

    def __str__(self):
        print("__STR__: This class serves to initialize and get the required info about a user.")


    def user_info(self) -> dict:
        timezone = execute_query("SELECT timezone FROM users WHERE telegram_id = ?", (self.uid,), True)[0]
        tasks_logged = execute_query("SELECT COUNT(id) FROM tasks WHERE user_id = ?", (self.uid,), True)[0]
        tasks_done = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = TRUE)", (self.uid,), True)[0]
        tasks_left = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = FALSE)", (self.uid,), True)[0]
        
        todays_date = datetime.strftime(get_user_local_time, FORMAT_STRING_DATE) + "%"
        todays_tasks = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND (created_at LIKE ?))",
                                    (self.uid, todays_date), True)[0]
        
        if execute_query("SELECT reminder_done_enabled FROM users WHERE telegram_id = ?", (self.uid,), True)[0] == "TRUE":
            reminder_done = execute_query("SELECT reminder_time_locale FROM reminders WHERE (user_id = ? AND type = 'DONE')")[0]
        else:
            reminder_done = "None set!"
        
        if execute_query("SELECT reminder_left_enabled FROM users WHERE telegram_id = ?", (self.uid,), True)[0] == "FALSE":
            reminder_left = execute_query("SELECT reminder_time_locale FROM reminders WHERE (user_id = ? AND type = 'LEFT')")[0]
        else:
            reminder_left = "None set!"

        user_info = {
            "timezone": timezone if timezone else "UTC",
            "tasks_logged": tasks_logged if tasks_logged else 0,
            "tasks_done": tasks_done if tasks_done else 0,
            "tasks_left": tasks_left if tasks_left else 0,
            "todays_tasks": todays_tasks if todays_tasks else 0,
            "reminder_done": reminder_done,
            "reminder_left": reminder_left
        }

        return user_info
    
        
    def get_user_tasks(uid: int) -> list:
        
        date = datetime.strftime(get_user_local_time(uid), FORMAT_STRING_DATE) + "%"
        query = (
            "SELECT * FROM tasks "
            "WHERE (user_id = ? AND (created_at LIKE ?)) "
            "ORDER BY priority ASC,created_at ASC "
        )
        try:
            today_tasks = execute_query(query, (uid, date), True)
        except sqlite3.Error:
            return 1
        else:
            return today_tasks

       
    def get_user_profile(self) -> str:
        info = self.user_info()

        formatted_strings = [
            f"👤 Your Telegram ID: {self.uid}",
            f"🌐 Your UTC Time Zone: {info.get('timezone')}",
            f"🔲 Total Tasks Logged: {info.get('tasks_logged')}",
            f"✅ Total Tasks Done: {info.get('tasks_done')}",
            f"❌ Total Tasks Left: {info.get('tasks_left')}",
            f"☀️ Today's Tasks: A number of {info.get('todays_tasks')} tasks",
            f"⌚ Achievement Reminder Is Set For: {info.get('reminder_done')}",
            f"⌛ Last Call Reminder Is Set For: {info.get('reminder_left')}"
        ]

        whole_string = "\n".join(formatted_strings)
        
        return whole_string
        