# /helpers/user_data_util_classes/user_class.py

# GENERAL PYTHON imports ->
from datetime import datetime, timedelta
import logging
import pytz
from sqlite3 import Error
# LOCAL imports ->
from config import FORMAT_STRING_DATE
from helpers.db_utils import execute_query
from reminder_handler_class import ReminderHandler
from task_handler_class import TaskHandler

logger = logging.getLogger(__name__)


class User:
    def __init__(self, uid: int):
        self._uid = uid
        self._is_a_user = self.is_a_user()
        if self._is_a_user:
            self.task = TaskHandler(self._uid)
            self.reminder = ReminderHandler(self._uid)
            self._info = self.user_info()
        else:
            self._info = None

    def __str__(self):
        print("__STR__: This class serves to initialize, validate, and get the required info about a user.")

    def is_a_user(self):
        user = execute_query('SELECT * FROM users WHERE telegram_id = ?', (self._uid,), True)

        if user is None:
            return False
        else:
            return True

    def is_timezone_valid(self, user_input: str) -> bool:
        return (user_input in pytz.all_timezones_set)

    def get_offset(self, offset_string: str) -> timedelta:
        offset_string = offset_string.upper().replace("UTC", "").strip()
        if not offset_string:
            return timedelta(0)

        sign = 1
        if offset_string.startswith('-'):
            sign = -1

        offset_string = offset_string[1:]

        parts = offset_string.split(':')
        hours = int(parts[0]) if parts[0] else 0
        minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0

        return timedelta(hours=hours * sign, minutes=minutes * sign)

    def get_user_local_time(self) -> datetime:
        try:
            user_tz_string = execute_query("SELECT IANA_timezone FROM users WHERE telegram_id = ?", (self._uid,), True)[0][0]
        except (TypeError, ValueError, IndexError, Error) as e:
            logger.error(f"No timezone accessible: {e}")
            user_tz_string = None

        if user_tz_string:
            user_tz = pytz.timezone(user_tz_string)
            return datetime.now(user_tz)
        else:
            logger.warning("No IANA timezone found, defaulting to UTC.")
            return datetime.now(pytz.utc)
        
    def user_info(self) -> dict:
        timezone = execute_query("SELECT utc_offset, IANA_timezone FROM users WHERE telegram_id = ?", (self._uid,), True)[0]
        tasks_logged = execute_query("SELECT COUNT(id) FROM tasks WHERE user_id = ?", (self._uid,), True)[0][0]
        tasks_done = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 1)", (self._uid,), True)[0][0]
        tasks_left = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 0)", (self._uid,), True)[0][0]
        
        todays_date = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        todays_tasks = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND (created_at LIKE ?))",
                                    (self._uid, todays_date,), True)[0][0]
        todays_tasks_done = execute_query(
            query = "SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 1 AND (created_at LIKE ?))",
            params = (self._uid, todays_date),
            fetch = True)[0][0]
        
        if execute_query("SELECT reminder_done_enabled FROM users WHERE telegram_id = ?", (self._uid,), True)[0][0] == 1:
            reminder_done = execute_query("SELECT reminder_time_locale FROM reminders WHERE (user_id = ? AND type = 'DONE')", (self._uid,), True)[0][0]
        else:
            reminder_done = None
        
        if execute_query("SELECT reminder_left_enabled FROM users WHERE telegram_id = ?", (self._uid,), True)[0][0] == 1:
            reminder_left = execute_query("SELECT reminder_time_locale FROM reminders WHERE (user_id = ? AND type = 'LEFT')", (self._uid,), True)[0][0]
        else:
            reminder_left = None

        user_info = {
            "utc_offset": timezone[0] if timezone else "UTC+00:00",
            "IANA_timezone": timezone[1] if timezone else "NULL",
            "tasks_logged": tasks_logged if tasks_logged else 0,
            "tasks_done": tasks_done if tasks_done else 0,
            "tasks_left": tasks_left if tasks_left else 0,
            "todays_tasks": todays_tasks if todays_tasks else 0,
            "todays_tasks_done": todays_tasks_done if todays_tasks_done else 0,
            "reminder_done": reminder_done,
            "reminder_left": reminder_left
        }

        return user_info
    
    def create_user_profile(self, user_input: str):
        user_tz = pytz.timezone(user_input)
        user_tz_raw = datetime.now(user_tz).strftime("%z")
        user_tz_offset = f"UTC{user_tz_raw[0:3]}:{user_tz_raw[3:]}"

        if not self.is_a_user():
            query = "INSERT INTO users VALUES (?, ?, ?, ?, ?)"
            params = (self._uid, user_tz_offset, user_input, 0, 0)
        else:
            query = "UPDATE users SET utc_offset = ?, IANA_timezone = ? WHERE telegram_id = ?"
            params = (user_tz_offset, user_input, self._uid)

        execute_query(query, params)

    def delete_user_profile(self):
        query_1 = "DELETE FROM users WHERE telegram_id = ?"
        query_2 = "DELETE FROM tasks WHERE user_id = ?"
        param = (self._uid,)

        try:
            execute_query(query_1, param)
        except Error as e:
            logger.error(f"No user with ID {self._uid} was accessible.")
        else:
            logger.info("User's row was successfully removed!")

        try:
            execute_query(query_2, param)
        except Error as e:
            logger.error("No tasks for the user with ID {self._uid} was accessible.")
        else:
            logger.info("User's tasks were successfully removed!")

    def get_user_profile(self) -> str:
        info = self.user_info()

        if info.get('reminder_done') is None:
            reminder_done = "None set!"
        else:
            reminder_done = info.get('reminder_done')

        if info.get('reminder_left') is None:
            reminder_left = "None set!"
        else:
            reminder_left = info.get('reminder_left')

        formatted_strings = [
            f"👤 Your Telegram ID: {self._uid}",
            f"🌐 Your UTC Offset: {info.get('utc_offset')} / {info.get('IANA_timezone')}",
            f"🔲 Total Tasks Logged: {info.get('tasks_logged')}",
            f"✅ Total Tasks Done: {info.get('tasks_done')}",
            f"❌ Total Tasks Left: {info.get('tasks_left')}",
            f"☀️ Today's Tasks Done: A number of {info.get('todays_tasks_done', 0)} tasks were marked done out of {info.get('todays_tasks', 0)}",
            f"⌚ Achievement Reminder is set for: {reminder_done}",
            f"⌛ Last Call Reminder is set for: {reminder_left}"
        ]

        whole_string = "\n".join(formatted_strings)
        
        return whole_string