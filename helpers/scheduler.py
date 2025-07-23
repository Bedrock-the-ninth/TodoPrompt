# common/scheduler.py

# GENERAL PYTHON imports ->
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime, timedelta
import logging
from pytz import timezone
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from telegram.helpers import escape_markdown
# DOMESTIC imports
from helpers.user_data_utils import User, get_user_local_time
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
        tasks_done_count = f"{user_at_hand.user_info().get('todays_tasks_done', 0)} / {user_at_hand.user_info().get('todays_tasks', "NaN")}"
        reminder_content += escape_markdown(f"You have completed *{tasks_done_count}* tasks so far today!", version=2)

    elif reminder_type == 'LEFT':
        reminder_content = escape_markdown(f"⏰ Last call reminder! Tasks still remaining:\n\n", version=2)
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


async def set_user_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, reminder_type_str: str = None) -> tuple:
    user_id = update.effective_chat.id
    user_input = update.message.text

    user_at_hand = User(user_id)
    user_iana_tz_str = user_at_hand.user_info().get('IANA_timezone')
    user_local_time = get_user_local_time(user_id)

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

    try:
        context.job_queue.scheduler.remove_job(job_id)
    except JobLookupError:
        pass
    else:
        logger.info(f"Removed existing reminder job: {job_id}")

    context.job_queue.scheduler.add_job(
        func = send_reminder_message,
        trigger = 'date',
        args = [context],
        id = job_id,
        replace_existing = True,
        trigger_args= {
            "run_date" : todays_reminder_time,
        },
    )
    logger.info(f"Scheduled reminder '{job_id}' for {todays_reminder_time}")

    del user_at_hand
    return (0, job_id, todays_reminder_time)
# <<< Scheduler Brain <<<
