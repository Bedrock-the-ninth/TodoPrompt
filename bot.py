# IMPORTS #
# GENERAL PYTHON imports ->
from dotenv import load_dotenv
import logging
from os import getenv
from pathlib import Path
# TELEGRAM BOT related imports ->
from telegram.ext import (ApplicationBuilder, PicklePersistence)
# DOMESTIC Imports ->
from handlers.start_menu_handler import get_setup_conversation_handler
from handlers.main_menu_handlers import get_main_menu_handler
import helpers.db_utils as helpers


# Using path for connecting the persistence file.
DATA_DIR = Path('data')
PERSISTENCE_FILE = DATA_DIR / "bot_data.pickle"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":

    # Load bot token from ./.env
    load_dotenv()
    TOKEN = getenv("BOT_TOKEN")

    # Initiate the DB
    helpers.db_initiator()
    persistence = PicklePersistence(filepath=PERSISTENCE_FILE)

    application = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
    application.add_handler(get_setup_conversation_handler)
    application.add_handler(get_main_menu_handler)

    application.run_polling()
