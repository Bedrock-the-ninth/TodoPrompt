# IMPORTS #
# GENERAL PYTHON imports ->
import logging
# APScheduler imports ->
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
# TELEGRAM BOT related imports ->
from telegram.ext import (ApplicationBuilder, PicklePersistence, JobQueue)
# DOMESTIC Imports ->
    # Bot TOKEN import ->
from config import TOKEN
    # Paths import ->
from config import DATABASE_FILE, PERSISTENCE_FILE
    # Main parts' handlers ->
from handlers.main.main_menu_handler import get_main_menu_handler
from handlers.main.start_conversation_handler import get_setup_conversation_handler
    # Tasks' handlers ->
from handlers.tasks.prompt_add_task_handler import get_prompt_add_task_handler
from handlers.tasks.prompt_check_task_handler import get_prompt_check_task_handler
from handlers.tasks.prompt_remove_task_handler import get_prompt_remove_task_handler
from handlers.tasks.task_menu_handler import get_task_menu_handler
    # Reminders' handlers ->
from handlers.reminders.reminders_menu_handler import get_reminders_menu_handler
from handlers.reminders.prompt_d_reminder_handler import get_prompt_d_reminder_handler
from handlers.reminders.prompt_l_reminder_handler import get_prompt_l_reminder_handler
    # Settings handler ->
from handlers.settings.settings_handler import get_settings_handler
import helpers.db_utils as helpers

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Initiate the DB
    helpers.db_initiator()
    persistence = PicklePersistence(filepath=PERSISTENCE_FILE)

    # Defining jobstore for APScheduler ->
    job_stores_config = {
        'default': {
            'type': 'sqlalchemy',
            'url': f'sqlite:///{DATABASE_FILE.resolve()}'
        }
    }

    ptb_job_queue = JobQueue()
    """
    Dividing the application and the build process allows for a more logical
    flow of things especially the main_menu and setup_convo assignment.
    This change was suggested by Gemini.
    """
    app_builder = ApplicationBuilder().token(TOKEN).persistence(persistence).job_queue(ptb_job_queue)

    setup_convo = get_setup_conversation_handler()
    main_menu = get_main_menu_handler()
    task_menu = get_task_menu_handler()
    reminders_menu = get_reminders_menu_handler()
    settings_menu = get_settings_handler()
    prompt_add_task = get_prompt_add_task_handler()
    prompt_remove_task = get_prompt_remove_task_handler()
    prompt_task_check = get_prompt_check_task_handler()
    prompt_d_reminder = get_prompt_d_reminder_handler()
    prompt_l_reminder = get_prompt_l_reminder_handler()


    application = app_builder.build()
    application.job_queue.scheduler.add_jobstore(SQLAlchemyJobStore(url=f"sqlite:///{DATABASE_FILE.resolve()}"))


    application.add_handlers(
        handlers = [
            setup_convo, 
            main_menu, 
            task_menu, 
            reminders_menu,
            settings_menu,
            prompt_add_task,
            prompt_remove_task,
            prompt_task_check,
            prompt_d_reminder,
            prompt_l_reminder
        ]
    )

    application.run_polling()
