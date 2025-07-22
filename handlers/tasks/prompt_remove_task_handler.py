# handlers/prompt_remove_task_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
    filters, 
    MessageHandler   
)
# DOMESTIC imports ->
from handlers.common.common_handlers import (
    close_all_convos, 
    return_to_tasks,
    delete_previous_menu,
    edit_previous_menu
)
from handlers.common.inline_keyboards_module import tasks_keyboard, subtasks_keyboard
from helpers.user_data_utils import User

# State Definition for ConversationHandlers
from config import VIEW_TASKS_STATE, PROMPT_REMOVE_TASK_STATE
# Initiating logger
logging = logging.getLogger(__name__)


# >>> Remove Task State Prompts >>>
async def prompt_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    edited_main_menu = query.message.message_id
    prior_main_menu = context.user_data['main_menu_message_id']

    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    user_tasks = user_at_hand.get_user_tasks()
    if user_tasks:
        user_tasks_string = "\n".join(user_tasks) 
    else:
        user_tasks_string = "\n".join("---NO TASKS ADDED YET---")

    suffix_string = "\n\nTo remove a task from the list below, just send the row number, I'll handle the rest ╰(*°▽°*)╯"
    whole_string = user_tasks_string + suffix_string
    remove_task_markup = subtasks_keyboard()

    if prior_main_menu == edited_main_menu:
        await edit_previous_menu(update, context, whole_string, remove_task_markup)
        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE
    else:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = edited_main_menu
        await edit_previous_menu(update, context, whole_string, remove_task_markup)

        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE


async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    user_tasks = user_at_hand.get_user_tasks()
    if user_tasks:
        user_tasks_string = "\n".join(user_tasks) 
    else:
        user_tasks_string = "\n".join("---NO TASKS ADDED YET---")
    text_string = f"Your tasks are as follows:\n{"\n".join(user_tasks_string)}"
    remove_task_markup = subtasks_keyboard()

    try:
        user_input = int(update.message.text) - 1
    except ValueError:
        logging.info(f"User entered an input that is not a number.")
        error_text_1 = text_string + "\n*❌Your input was not a parsable integer. Try again!*"

        await edit_previous_menu(update, context, error_text_1, remove_task_markup)
        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE
    except TypeError:
        logging.info(f"User entered an empty input that is probably of type <NoneType>.")
        error_text_2 = text_string + "\n*❌Your input was not a parsable integer. Try again!*"

        await edit_previous_menu(update, context, error_text_2, remove_task_markup)
        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE
    else:
        if not 0 <= user_input < len(user_tasks):
            logging.info(f"User entered an input out of their tasklist range.")
            error_text_3 = text_string + "\n*❌Your input was out of range. Try again!*"

            await edit_previous_menu(update, context, error_text_3, remove_task_markup)
            del user_at_hand
            return PROMPT_REMOVE_TASK_STATE
        else:
            to_be_removed_string: str = user_tasks[user_input]
            to_be_removed_task =  to_be_removed_string.split('--')[1].strip()

            result = user_at_hand.remove_user_task(to_be_removed_task)

            if result == 0:
                logging.info(f"Task `{to_be_removed_task}` was successfully removed for user {user_id}")
                
                refetch_list = user_at_hand.get_user_tasks()
                if refetch_list:
                    refetch_string = "\n".join(refetch_list) 
                else:
                    refetch_string = "\n".join("---NO TASKS ADDED YET---")

                success_string = "\n*✅Your task was removed successfully. If you wish you can remove another (assuming there are still tasks to remove.)*" + refetch_string
                task_menu_markup = tasks_keyboard()

                await edit_previous_menu(update, context, success_string, task_menu_markup)
                
                del user_at_hand
                return ConversationHandler.END
            else:
                logging.info("Unsuccessful attempt to remove the task")
                error_text_4 = text_string + "\n*❌Unsuccessful attempt to remove your task. Try again!*"

                await edit_previous_menu(update, context, error_text_4, remove_task_markup)
                del user_at_hand
                return PROMPT_REMOVE_TASK_STATE
                
            

# <<< Remove Task State Prompts <<<
def get_prompt_remove_task_handler():
    return ConversationHandler(
        entry_points = {
            CallbackQueryHandler(pattern='^tasks_remove$', callback=prompt_remove_task),
        },
        states = {
            PROMPT_REMOVE_TASK_STATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, remove_task),
                CallbackQueryHandler(pattern='^subtasks_return$', callback=return_to_tasks)
            ]
        },
        fallbacks = {
            CommandHandler('cancel', close_all_convos)
        },
        map_to_parent = {
            ConversationHandler.END : VIEW_TASKS_STATE
        },
        allow_reentry = True,
    )