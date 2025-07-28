# /helpers/user_data_util_classes/reminder_handler_class.py

# GENERAL PYTHON imports ->
import logging
from sqlite3 import Error
# LOCAL imports ->
from helpers.db_utils import execute_query

logger = logging.getLogger(__name__)


class ReminderHandler:
    def __init__(self, uid: int):
        self.uid = uid

    def __str__(self):
        print("__STR__: This class serves to add, get, and remove reminders to and from the database.")

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
            parameters = (self._uid, reminder_type, reminder_time)
        else:
            query = "UPDATE reminders SET type = ?, reminder_time_locale = ? WHERE user_id = ?"
            parameters = (reminder_type, reminder_time, self._uid)

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
