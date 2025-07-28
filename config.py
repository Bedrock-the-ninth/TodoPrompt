# /config.py

# Load TOKEN from .env file ->
from dotenv import load_dotenv
from os import getenv

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

# Loading database and pickle filepaths:
from pathlib import Path

DATA_DIR = Path('data')
PERSISTENCE_FILE = DATA_DIR / "bot_data.pickle"
DATABASE_FILE = DATA_DIR / "database.db"

# Global Formatting Strings used for datetime.strftime ->
FORMAT_STRING_C = "%Y-%m-%d %H:%M:%S"
FORMAT_STRING_DATE = "%Y-%m-%d"
FORMAT_STRING_TIME = "%H:%M:%S"

# ConversationHandler States ->
GET_TIMEZONE_STATE = 0

VIEW_MENU = 100
VIEW_PROF_STATE = 101

VIEW_TASKS_STATE = 200
PROMPT_ADD_TASK_STATE = 201
PROMPT_REMOVE_TASK_STATE = 202
PROMPT_CHECK_TASK_STATE = 203

VIEW_REMINDERS_STATE = 300
PROMPT_D_REMINDER_STATE = 301
PROMPT_L_REMINDER_STATE = 302

VIEW_SETTINGS = 400
RESET_TIMEZONE = 401