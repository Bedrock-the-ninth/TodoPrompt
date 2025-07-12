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
from handlers.inline_keyboards_module import tasks_keyboard, subtasks_keyboard
from handlers.main_menu_handlers import close_all_convos
from helpers.user_data_utils import User

# State Definition for ConversationHandlers
from config import VIEW_TASKS_STATE, PROMPT_REMOVE_TASK_STATE
# Initiating logger
logging = logging.getLogger(__name__)


async def return_to_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    task_menu = context.user_data.get('main_menu_message_id', None)
    user_at_hand = User(user_id)
    tasks_markup = tasks_keyboard()

    if task_menu and context.user_data['edited_main_menu_id']:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=task_menu)
        except Exception as e:
            logging.info(f"{e}: The menu didn't exist or something.")
    else:
        user_tasks = "\n".join(user_at_hand.get_user_tasks())
        if not user_tasks.strip():
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = context.user_data['edited_main_menu_id'],
                text = "No tasks are added yet. Try adding one by touching the button \"➕ Add\""
                " or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2",
                reply_markup = tasks_markup
            )
        else:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = context.user_data['edited_main_menu_id'],
                text = f"Tasks:\n{user_tasks}",
                reply_markup = tasks_markup
            )
    
    del user_at_hand
    context.user_data['main_menu_message_id'] = context.user_data['edited_main_menu_id']

    return ConversationHandler.END


# >>> Remove Task State Prompts >>>
async def prompt_remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    edited_main_menu = query.message.message_id
    prior_main_menu = context.user_data['main_menu_message_id']

    text_string = f"Your tasks are as follows:\n{"\n".join(user_at_hand.get_user_tasks())}"
    "\n\nJust send the row number of the one you wish to delete."

    remove_task_markup = subtasks_keyboard

    if prior_main_menu == edited_main_menu:
        try:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = edited_main_menu,
                text = text_string,
                reply_markup = remove_task_markup
            )
        except Forbidden:
            logging.info(f"Bot is blocked by the user with ID {user_id}.")
        except Exception as e:
            logging.info(f"{e}: An unknown error happened.")
        else:
            del user_at_hand
            return PROMPT_REMOVE_TASK_STATE
    else:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prior_main_menu)
        except BadRequest:
            logging.info(f"Main menu with the ID {prior_main_menu} doesn't exist.")
        except Forbidden:
            logging.info(f"Bot was blocked by user with the ID {user_id}")
        except Exception as e:
            logging.info(f"{e}: An unknown error happened.")
        else:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = edited_main_menu,
                text = text_string,
                reply_markup = remove_task_markup
            )

            context.user_data['main_menu_message_id'] = edited_main_menu
            logging.info(f"New main menu with ID {edited_main_menu} was logged.")

            del user_at_hand
            return PROMPT_REMOVE_TASK_STATE


async def remove_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    user_tasks = user_at_hand.get_user_tasks()

    prior_main_menu = context.user_data['main_menu_message_id']
    text_string = f"Your tasks are as follows:\n{"\n".join(user_tasks)}"
    remove_task_markup = subtasks_keyboard

    try:
        user_input = int(update.message.text)
    except ValueError:
        logging.info(f"User entered an input that is not a number.")

        await context.bot.edit_message_text(
            chat_id = user_id,
            message_id = prior_main_menu,
            text = text_string + "\n*❌Your input was not a parsable integer. Try again!*",
            reply_markup = remove_task_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE

    except TypeError:
        logging.info(f"User entered an empty input that is probably of type <NoneType>.")

        await context.bot.edit_message_text(
            chat_id = user_id,
            message_id = prior_main_menu,
            text = text_string + "\n*❌Your input was not a parsable integer. Try again!*",
            reply_markup = remove_task_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        del user_at_hand
        return PROMPT_REMOVE_TASK_STATE
    
    else:
        if not 0 < user_input < len(user_tasks):
            logging.info(f"User entered an input out of their tasklist range.")
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = prior_main_menu,
                text = text_string + "\n*❌Your input was out of range. Try again!*",
                reply_markup = remove_task_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            del user_at_hand
            return PROMPT_REMOVE_TASK_STATE
        else:
            to_be_removed_string: str = user_tasks[user_input]
            to_be_removed_task =  to_be_removed_string.split('--')[1].strip()

            result = user_at_hand.remove_user_task(to_be_removed_task)

            if result == 0:
                logging.info(f"Task `{to_be_removed_task}` was successfully removed for user {user_id}")
                
                await context.bot.edit_message_text(
                    chat_id = user_id,
                    message_id = prior_main_menu,
                    text = "\n*✅Your task was removed successfully. If you wish you can remove another (assuming there are still tasks to remove.)*" + text_string,
                    reply_markup = remove_task_markup,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                del user_at_hand
                return PROMPT_REMOVE_TASK_STATE
            else:
                logging.info("Unsuccessful attempt to remove the task")

                await context.bot.edit_message_text(
                    chat_id = user_id,
                    message_id = prior_main_menu,
                    text = text_string + "\n*❌Unsuccessful attempt to remove your task. Try again!*",
                    reply_markup = remove_task_markup,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                del user_at_hand
                return PROMPT_REMOVE_TASK_STATE
                
            

# <<< Remove Task State Prompts <<<
def get_prompt_remove_task():
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