# /helpers/user_data_util_classes/time_module.py

# GENERAL PYTHON imports ->
from datetime import datetime
import logging
import pytz
from sqlite3 import Error
# LOCAL imports ->
from helpers.db_utils import execute_query

logger = logging.getLogger(__name__)


class TimeManager:
    """A class with two methods to validate time zone and get user's local time

    This class is used particularly in :module:task_module and in a special \
    case, in the :module:user_module for setting up time zone.
    """
    def __init__(self, uid: int):
        self._uid = uid

    def __str__(self):
        print("__STR__: This class serves handle time and time zone methods.")

    def is_timezone_valid(self, user_input: str) -> bool:
        return (user_input in pytz.all_timezones_set)

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