# /helpers/user_data_util_classes/user_module.py

# GENERAL PYTHON imports ->
from datetime import datetime, timedelta
import logging
import pytz
from sqlite3 import Error
# LOCAL imports ->
from config import FORMAT_STRING_DATE
from helpers.db_utils import execute_query
from .reminder_module import ReminderManager
from .task_module import TaskManager
from .time_module import TimeManager

logger = logging.getLogger(__name__)


class User:
    """User class is at the heart of this bot
    
    This class is the most crucial throughout this bot as it controls the \
    data flow from and back to user. From managing timezone and getting users' \
    local time; to handling input and marked done tasks; and to setting and managing \
    reminders on the database.
    """
    def __init__(self, uid: int):
        self._uid = uid
        self._is_a_user = self.is_a_user()
        if self._is_a_user: # Only if user has setup timezone, initiate task and reminder manager.
            self.task = TaskManager(self._uid)
            self.time = self.task.time
            self.reminder = ReminderManager(self._uid)
            self._info = self.user_info()
        else: # Time manager is initiated either way for setting up timezone
            self.time = TimeManager(self._uid) 
            self._info = None

    def __str__(self):
        print("__STR__: This class serves to initialize, validate, and get the required info about a user.")

    def is_a_user(self):
        """Checking to see if user exists on the database based on self._uid

        Returns:
            bool: If user is already on the database and associated with a timezone \
            the return value will be True. Otherwise, it will be False
        """         
        user = execute_query('SELECT * FROM users WHERE telegram_id = ?', (self._uid,), True)

        if user is None:
            return False
        else:
            return True
        
    def user_info(self) -> dict:
        """Collecting all of the info on one user.

        This method searches *users*, *tasks*, and *reminders* tables \
        on the database and stores them in a dictionary for later use in \
        different parts of the bot.

        Returns:
            dict: Returns a dictionary of nine main keys consisting of: \
            *'utc_off'*, *'IANA_timezone'*, *'tasks_logged'*, *'tasks_done'*, \
            *'tasks_left'*, *'todays_tasks'*, *'todays_tasks_done'*, *'reminder_done'*, \
            *'reminder_left'*
        """
        timezone = execute_query("SELECT utc_offset, IANA_timezone FROM users WHERE telegram_id = ?", (self._uid,), True)[0]
        tasks_logged = execute_query("SELECT COUNT(id) FROM tasks WHERE user_id = ?", (self._uid,), True)[0][0]
        tasks_done = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 1)", (self._uid,), True)[0][0]
        tasks_left = execute_query("SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 0)", (self._uid,), True)[0][0]
        
        todays_date = datetime.strftime(self.time.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        todays_tasks = execute_query(
            query = "SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND (created_at LIKE ?))",
            params = (self._uid, todays_date,), 
            fetch = True
        )[0][0]
        todays_tasks_done = execute_query(
            query = "SELECT COUNT(id) FROM tasks WHERE (user_id = ? AND is_done = 1 AND (created_at LIKE ?))",
            params = (self._uid, todays_date),
            fetch = True
        )[0][0]
        
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
        """Adds the user's telegram id, along with timezone to the database

        Args:
            user_input (str): Takes in the input user IANA time zone
        """
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
        """Removes user's data from *users* and *tasks* tables 

        This method deletes all exisiting data on a user from two tables.\
        Removing from the data from the table *reminders* is up to \
        :method:unset_user_reminder function within the scheduler module.

        See Also: :module:scheduler:method:unset_user_reminder 
        """
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
        """Formats user info into profile ready data

        This function takes the data in the info dictionary returned \
        from the :method:self.user_info

        Returns:
            str: Returns a formatted string ready to be put into the \
            main_menu_handler's profile section.
        """
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