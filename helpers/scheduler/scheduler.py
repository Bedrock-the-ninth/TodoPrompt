# /helpers/scheduler.py

# GENERAL PYTHON imports ->
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
from pytz import timezone
# TELEGRAM BOT imports ->
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
# LOCAL imports ->
from config import FORMAT_STRING_C
from helpers.user_data_util_classes.user_module import User
from helpers.scheduler.send_reminder_message import send_reminder_runner


logger = logging.getLogger(__name__)



# NOTE:
## In prior published versions, I tried to go with Telegram.JobQueue
## that natively uses APScheduler to queue the jobs and well, create jobstores.
## The catch with that approach was that, when connected to a database (not MemoryJobStore),
## it had to serilize (create weakref objects through PicklePersistence) to keep track.
## Therefore nothing but clean objects (Python native types like str, int) could have been
## passed to the send_reminder_message that was developed also in this file. And guess what?
## It needed the context but the JobQueue was wrapped around it and it couldn't recieve no
## unclean objects. Now, send_reminder_message.py holds a none-async function that instantiates
## it's own BOT object and does not need the context to be passed down to it. Also the (un)set_user_reminder
## functions had to get in touch directly with scheduler (APScheduler) instead of 
## using python-telegram-bot[job_queue] PTB objects. Theses changes were suggested by OpenAI's ChatGPT 4.O.


# >>> Scheduler Logic >>>
async def set_user_reminder(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        reminder_type_str: str = None
    ) -> tuple[int, str | None]:
    """This function sets a APScheduler Job object and fires it when \
    the determined trigger time comes.

    Args:
        update (Update): Telegram's Update object
        context (ContextTypes.DEFAULT_TYPE): Telegram's ContextType object
        reminder_type_str (str, optional): 'DONE' or 'LEFT'. Defaults to None.

    Returns:
        tuple(int, str | None): Returns a tuple, first character of which indicates \
        sucess or failure (0 and 1 respectively). Depending on that first index, \
        if it is a sucess, the job_id that was set and also the time for which the \
        reminder was set would follow in order after that integer as strings.
    """
    user_id = update.effective_chat.id
    user_input = update.message.text

    user_at_hand = User(user_id)
    user_iana_tz_str = user_at_hand._info.get('IANA_timezone')
    user_local_time = user_at_hand.time.get_user_local_time()

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
            # Set for a day after if user's local time passed the reminder's
            todays_reminder_time += timedelta(days=1)

    else:
        del user_at_hand
        return (1, None)
    
    # Setting up job info
    job_id = f"reminder_{user_id}_{reminder_type_str}"

    # Remove job if it exists to avoid duplicates and exceptions
    existing_jobs = context.job_queue.scheduler.get_jobs(jobstore='default')
    jobs_to_remove = [job for job in existing_jobs if job.id == job_id]

    if not jobs_to_remove:
        logger.info(f"No existing job found with name: {job_id}")
    else:
        for job in jobs_to_remove:
            job.remove()
        logger.info(f"Removed existing reminder job(s) with name: {job_id}")

    # To avoid passing context (not a clean object) 
    # trigger a standalone callback function
    context.job_queue.scheduler.add_job(
        func = send_reminder_runner,
        trigger = IntervalTrigger(days=1, start_date=todays_reminder_time),
        args = [user_id, reminder_type_str],
        id = job_id,
        replace_existing = True,
        name = job_id,
        misfire_grace_time = 60,
    )
    # Log the reminder onto *reminders* data table as well for a more sound structure ->
    user_at_hand.reminder.log_reminder(reminder_type_str, todays_reminder_time.strftime(FORMAT_STRING_C))
    logger.info(f"Scheduled reminder '{job_id}' for {todays_reminder_time}")

    del user_at_hand
    return (0, job_id, todays_reminder_time)


async def unset_user_reminder(
        update: Update, 
        context: ContextTypes.DEFAULT_TYPE, 
        reminder_type_str: str
    ) -> tuple[int | str]:
    """This function clears the APScheduler's scheduled job \
    and removes all signs of it from database (Uses user_data_util\
    _classes to do the latter)

    Args:
        update (Update): Telegram's Update object
        context (ContextTypes.DEFAULT_TYPE): Telegram's ContextType object
        reminder_type_str (str, optional): 'DONE' or 'LEFT'.

    Returns:
        tuple(int | str): The first return value would be an integer that \
        determines the success of the operation. If a 0 (indicating success) \
        is returned, the values to follow are database reminder removal confirmation\
        (0 for success and 1 for failure) and the job_id that was removed from the \
        APScheduler's job_queue.
    """
    
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    
    job_schedule_removal = 0
    database_reminder_removal = 0
        
    assumed_job_id = f"reminder_{user_id}_{reminder_type_str}"

    existing_jobs = context.job_queue.scheduler.get_jobs(jobstore='default')
    jobs_to_remove = [job for job in existing_jobs if job.id == assumed_job_id]

    if not jobs_to_remove:
        logger.info(f"No existing job found with name: {assumed_job_id}")
    else:
        for job in jobs_to_remove:
            job.remove()
        logger.info(f"Removed existing reminder job(s) with name: {assumed_job_id}")
        job_schedule_removal = 1

    database_deletion_result = user_at_hand.reminder.delete_reminder(reminder_type_str)
    if database_deletion_result == 0:
        logger.info(f"Job with ID {assumed_job_id} was removed from database.")
        database_reminder_removal = 1
    else:
        logger.warning(f"Unsuccessful attempt on removing the reminder entry from database.")
    
    return (job_schedule_removal, database_reminder_removal, assumed_job_id)
# <<< Scheduler Logic <<<
