# IMPORTS #
# GENERAL PYTHON imports ->
from dotenv import load_dotenv
import logging
from os import getenv
from pathlib import Path
# TELEGRAM BOT related imports ->
from telegram.ext import (ApplicationBuilder, PicklePersistence)
# DOMESTIC Imports ->
from handlers.main_menu_handlers import get_main_menu_handler
from handlers.prompt_add_task_handler import get_prompt_add_task_handler
from handlers.prompt_remove_task_handler import get_prompt_remove_task_handler
from handlers.start_conversation_handler import get_setup_conversation_handler
from handlers.task_menu_handlers import get_task_menu_handler
import helpers.db_utils as helpers


# Using path for connecting the persistence file.
DATA_DIR = Path('data')
PERSISTENCE_FILE = DATA_DIR / "bot_data.pickle"

# Enable logging
# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
# )
# logger = logging.getLogger(__name__)


if __name__ == "__main__":

    # Load bot token from ./.env
    load_dotenv()
    TOKEN = getenv("BOT_TOKEN")

    # Initiate the DB
    helpers.db_initiator()
    persistence = PicklePersistence(filepath=PERSISTENCE_FILE)

    """
    Dividing the application and the build process allows for a more logical
    flow of things especially the main_menu and setup_convo assignment.
    This change was suggested by Gemini.
    """

    app_builder = ApplicationBuilder().token(TOKEN).persistence(persistence)

    setup_convo = get_setup_conversation_handler()
    main_menu = get_main_menu_handler()
    task_menu = get_task_menu_handler()
    prompt_add_task = get_prompt_add_task_handler()
    prompt_remove_task = get_prompt_remove_task_handler()

    application = app_builder.build()

    application.add_handler(setup_convo)
    application.add_handler(main_menu)
    application.add_handler(task_menu)
    application.add_handler(prompt_add_task)
    application.add_handler(prompt_remove_task)

    application.run_polling()
