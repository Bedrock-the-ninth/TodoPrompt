# /helpers/scheduler/send_reminder_message.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports
from telegram import Bot
from telegram.helpers import escape_markdown
# LOCAL IMPORTS
from helpers.user_data_util_classes.user_module import User
from config import TOKEN

logger = logging.getLogger(__name__)

def determine_message(user_id: int, reminder_type: str) -> str:
    """Based on reminder_type ('DONE' or 'LEFT') and user's tasks \
    this function creates the proper reminder message text.

    Args:
        user_id (int): Telegram user id
        reminder_type (str): 'DONE' or 'LEFT'

    Returns:
        str: Proper reminder message content
    """
    user_at_hand = User(user_id)
    user_tasks = user_at_hand.task.get_user_tasks()
    info = user_at_hand._info

    if reminder_type == 'DONE':
        reminder_content = escape_markdown(f"🎉 Your achievement reminder for today! Here's your summary:\n\n", version=2)
        if not user_tasks:
            reminder_content += escape_markdown(f"No tasks were logged today! Try adding some new ones.", version=2)
        else:
            tasks_done_count = f"{info.get('todays_tasks_done', 0)} / {info.get('todays_tasks', "NaN")}"
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

    del user_at_hand
    return reminder_content


async def send_reminder_runner(user_id: int, reminder_type: str):
    """This function instantiates a telegram Bot object (standalone) \
    and sends a message when triggered by the scheduler logic and APScheduler.

    Args:
        user_id (int): Telegram user id
        reminder_type (str): 'DONE' or 'LEFT'
    """
    bot = Bot(token=TOKEN)
    reminder_content = determine_message(user_id, reminder_type)

    try:
        await bot.send_message(user_id, reminder_content, parse_mode="MarkdownV2")
    except Exception as e:
        logger.error(f"Could not send reminder: {e}")
    logger.info(f"Reminder sent for user {user_id} of type {reminder_type}.")