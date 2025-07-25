from config import FORMAT_STRING_C, FORMAT_STRING_DATE, FORMAT_STRING_TIME
from datetime import datetime, timezone, timedelta
from helpers.db_utils import execute_query
import logging
import pytz
from sqlite3 import Error

logger = logging.getLogger(__name__)


class User:
    def __init__(self, uid: int):
        self._uid = uid
        self._is_a_user = self.is_a_user()
        if self._is_a_user:
            self._info = self.user_info()
        else:
            self._info = None

    def __str__(self):
        print("__STR__: This class serves to initialize and get the required info about a user.")

    def is_a_user(self):
        user = execute_query('SELECT * FROM users WHERE telegram_id = ?', (self._uid,), True)

        if user is None:
            return False
        else:
            return True

    def is_timezone_valid(self, user_input: str) -> bool:
        return (user_input in pytz.all_timezones_set)

    def create_user_profile(self, user_input: str):
        user_tz = pytz.timezone(user_input)
        user_tz_raw = datetime.now(user_tz).strftime("%z")
        user_tz_offset = f"UTC{user_tz_raw[0:3]}:{user_tz_raw[3:]}"

        execute_query("INSERT INTO users VALUES (?, ?, ?, ?, ?)", params=(self._uid, user_tz_offset, user_input, 0, 0))

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
        
    def get_user_tasks(self) -> list | None:
        
        date = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        query = (
            "SELECT * FROM tasks "
            "WHERE (user_id = ? AND (created_at LIKE ?)) "
            "ORDER BY priority ASC,created_at ASC "
        )
        try:
            today_tasks = execute_query(query, (self._uid, date), True)
        except Error:
            return None
        else:
            if today_tasks:
                formatted_list = []
                for (index, task) in enumerate(today_tasks):
                    priority = "🔥" * task[3]
                    is_done = "✅" if task[4] == 1 else "🔲"
                    formatted_string = f"|{"0" if index <= 8 else ""}{index+1}|-- {task[2]} -- {priority} -- ({is_done})"
                    formatted_list.append(formatted_string)

                return formatted_list
            else:
                return None
           
    def add_user_task(self, task: str, priority: int) -> int:

        user_current_time_string = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_C)

        if priority in [1, 2, 3]:
            try:
                execute_query("INSERT INTO tasks (user_id, content, priority, created_at) VALUES (?, ?, ?, ?)",
                            (self._uid, task, priority, user_current_time_string))
            except Error:
                return 2
        else:
            return 1

        return 0
    
    def remove_user_task(self, task: str) -> int:
        try:
            execute_query("DELETE FROM tasks WHERE (user_id = ? AND content = ?)", (self._uid, task))
        except Error:
            return 1
        
        return 0
    
    def mark_done_and_return_new_list(self, task: str) -> list | int | None:
        user_local_date = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        update_query = "UPDATE tasks SET is_done = TRUE WHERE (user_id = ? AND content = ? AND (created_at LIKE ?))"
        try:
            execute_query(update_query, (self._uid, task, user_local_date))
        except Error:
            return 1
        else:
            refetched_user_tasks = self.get_user_tasks()
            return refetched_user_tasks

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
            f"⌚ Achievement Reminder Is Set For: {reminder_done}",
            f"⌛ Last Call Reminder Is Set For: {reminder_left}"
        ]

        whole_string = "\n".join(formatted_strings)
        
        return whole_string
    
    def check_reminder_state(self, reminder_type, state) -> int:
        column_value = 'reminder_done_enabled' if reminder_type == "DONE" else 'reminder_left_enabled'
        query = f"SELECT {column_value} FROM users WHERE telegram_id = ?"
        parameters = (self._uid,)

        try:
            result = execute_query(query, parameters, fetch=True)
        except Error as e:
            logger.error(f"{e}-> Something went wrong checking user's reminder state.")
            return 2
        else:
            if not result:
                logger.warning("No reminder state found.")
                return 2
            else:
                return 0 if result[0][0] == state else 1

    def set_reminder_state(self, reminder_type, state) -> int:
        column_value = "reminder_done_enabled" if reminder_type == "DONE" else "reminder_left_enabled"
        query = f"UPDATE users SET {column_value} = ? WHERE telegram_id = ?"
        parameters = (state, self._uid)

        try:
            execute_query(query, parameters)
        except Error as e:
            logger.error(f"{e}-> Something went wrong updating user's reminder flag.")
            return 1
        else:
            logger.info("User's reminder flag was successfully updated!")
            return 0
    
    def log_reminder(self, reminder_type, reminder_time) -> int:
        reminder_state = self.check_reminder_state(reminder_type, 1)

        if reminder_state != 0:
            query = "INSERT INTO reminders VALUES (?, ?, ?)"
        else:
            query = "UPDATE reminders SET VALUES (?, ?, ?)"

        parameters = (self._uid, reminder_type, reminder_time)
        try:
            execute_query(query, parameters)
        except Error as e:
            logger.error(f"{e}-> Something went wrong adding user's reminder to the database.")
            return 1
        else:
            logger.info(f"User's reminder was added to the database!")
            state_update = self.set_reminder_state(reminder_type, 1)
            if state_update != 0:
                logger.warning("Failed to update user's reminder state.")
            return 0

    def delete_reminder(self, reminder_type) -> int:
        reminder_state = self.check_reminder_state(reminder_type, 1)

        if reminder_state != 0:
            logger.warning("No active reminder found to delete.")
            return 1
        else:
            query = "DELETE FROM reminders WHERE user_id = ? AND type = ?"
            parameters = (self._uid, reminder_type)

            try:
                execute_query(query, parameters)
            except Error as e:
                logger.error(f"{e}-> Something went wrong deleting user's reminder from the database.")
                return 1
            else:
                logger.info("User's reminder was successfully deleted from the database!")
                state_update = self.set_reminder_state(reminder_type, 0)
                if state_update != 0:
                    logger.warning("Failed to update user's reminder state.")
                return 0