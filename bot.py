# IMPORTS #
# To load token ->
from dotenv import load_dotenv
from os import getenv
# To log when shit hits the fan ->
import logging
# Telegram Bot related imports ->
from telegram.ext import (ApplicationBuilder, PicklePersistence)
# Handler modules ->
from handlers.start_conversation import get_setup_conversation_handler
from handlers.main_menu_handlers import get_main_menu_handler
# Helpers module ->
import helpers


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

    persistence_file = "bot_data.pickle"
    persistence = PicklePersistence(filepath=persistence_file)

    application = ApplicationBuilder().token(TOKEN).persistence(persistence).build()

    application.add_handler(get_setup_conversation_handler)
    application.add_handler(get_main_menu_handler)

    application.run_polling()
