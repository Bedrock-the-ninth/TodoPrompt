# helpers/scheduler.py

# GENERAL PYTHON imports ->
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime, timedelta
import logging
from pytz import timezone
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from telegram.helpers import escape_markdown
# DOMESTIC imports
from config import FORMAT_STRING_C
from helpers.user_data_utils import User
from handlers.common.common_handlers import (
    send_reminder, 
    send_new_menu, 
)

logger = logging.getLogger(__name__)

# >>> Scheduler Brain >>>
async def send_reminder_message(context: ContextTypes.DEFAULT_TYPE):
    """
    This function is called by APScheduler when a reminder job fires.
    It sends the reminder message to the user.
    """
    job = context.job

    user_id = job.chat_id
    reminder_type = job.data['reminder_type']

    user_at_hand = User(user_id)
    user_tasks = user_at_hand.get_user_tasks()

    if reminder_type == 'DONE':
        reminder_content = escape_markdown(f"🎉 Your achievement reminder for today! Here's your summary:\n\n", version=2)
        if not user_tasks:
            reminder_content += escape_markdown(f"No tasks were logged today! Try adding some new ones.", version=2)
        else:
            tasks_done_count = f"{user_at_hand._info.get('todays_tasks_done', 0)} / {user_at_hand._info.get('todays_tasks', "NaN")}"
            tasks_done_list = [task for task in user_tasks if "✅" in task]
            reminder_content += escape_markdown(f"You have completed *{tasks_done_count}* tasks so far today:", version=2)
            reminder_content += "\n".join([escape_markdown(s, version=2) for s in tasks_done_list])

    elif reminder_type == 'LEFT':
        reminder_content = escape_markdown(f"⏰ Last call reminder! Tasks still remaining:\n\n", version=2)
        if not user_tasks :
            reminder_content += escape_markdown("No tasks were logged today! Try adding some new ones.", version=2)
        else:
            tasks_left_list = [task for task in user_tasks if "✅" not in task]
            if tasks_left_list:
                reminder_content += "\n".join([escape_markdown(s, version=2) for s in tasks_left_list])
            else:
                reminder_content += escape_markdown("Great job! All tasks are done for today!", version=2)
    
    # No need for Update object for BOT INITIATED interactions
    await send_reminder(
        context = context,
        content = reminder_content,
        markup = None,
        parse_mode = ParseMode.MARKDOWN_V2,
        chat_id_override = user_id
    )
    
    del user_at_hand
    logger.info(f"Reminder sent for user {user_id} of type {reminder_type}.")


async def set_user_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, reminder_type_str: str = None) -> tuple[int, str | None]:
    user_id = update.effective_chat.id
    user_input = update.message.text

    user_at_hand = User(user_id)
    user_iana_tz_str = user_at_hand._info.get('IANA_timezone')
    user_local_time = user_at_hand.get_user_local_time()

    reminder_hour, reminder_minute = map(int, user_input.split(":"))

    if user_iana_tz_str:
        user_iana_tz = timezone(user_iana_tz_str)

        todays_reminder_time = user_iana_tz.localize(datetime.now().replace(
            hour = reminder_hour,
            minute = reminder_minute,
            second = 0,
            microsecond = 0
        ))
        
        if todays_reminder_time <= user_local_time:
            todays_reminder_time += timedelta(days=1)

    else:
        del user_at_hand
        return (1, None)
    
    # Setting up job info
    job_id = f"reminder_{user_id}_{reminder_type_str}"

    # Remove job if it exists
    existing_jobs = context.job_queue.get_jobs_by_name(job_id)
    if existing_jobs:
        for job in existing_jobs:
            job.schedule_removal()
        logger.info(f"Removed existing reminder job(s) with name: {job_id}")
    else:
        logger.info(f"No existing job found with name: {job_id}")

    context.job_queue.run_repeating(
        callback = send_reminder_message,
        interval = timedelta(days=1),
        first = todays_reminder_time,
        chat_id = user_id,
        name = job_id,
        data = {"reminder_type" : reminder_type_str},
    )
    user_at_hand.log_reminder(reminder_type_str, todays_reminder_time.strftime(FORMAT_STRING_C))
    logger.info(f"Scheduled reminder '{job_id}' for {todays_reminder_time}")
    
    jobs = context.job_queue.scheduler.get_jobs()
    logger.info(f"These jobs are scheduled: {jobs}")

    del user_at_hand
    return (0, job_id, todays_reminder_time)


async def unset_user_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, reminder_type_str: str) -> tuple[int | str]:
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    
    job_schedule_removal = 0
    database_reminder_removal = 0
        
    jobs = context.job_queue.scheduler.get_jobs()
    logger.info(f"These jobs are scheduled: {jobs}")

    assumed_job_id = f"reminder_{user_id}_{reminder_type_str}"

    existing_jobs = context.job_queue.get_jobs_by_name(assumed_job_id)

    if not existing_jobs:
        logger.info(f"No existing job found with name: {assumed_job_id}")
    else:
        for job in existing_jobs:
            job.schedule_removal()
        logger.info(f"Removed existing reminder job(s) with name: {assumed_job_id}")
        job_schedule_removal = 1

    database_deletion_result = user_at_hand.delete_reminder(reminder_type_str)
    if database_deletion_result == 0:
        logger.info(f"Job with ID {assumed_job_id} was removed from database.")
        database_reminder_removal = 1
    else:
        logger.warning(f"Unsuccessful attempt on removing the reminder entry from database.")
        return (2, assumed_job_id)
    
    return (job_schedule_removal, database_reminder_removal, assumed_job_id)
# <<< Scheduler Brain <<<
