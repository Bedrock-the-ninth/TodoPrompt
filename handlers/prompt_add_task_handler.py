# handlers/prompt_add_task_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
    filters, 
    MessageHandler   
)
# DOMESTIC imports ->
from handlers.common_handlers import close_all_convos, return_to_tasks
from handlers.inline_keyboards_module import tasks_keyboard, subtasks_keyboard
from helpers.user_data_utils import User

# State Definition for ConversationHandlers
from config import VIEW_TASKS_STATE, PROMPT_REMOVE_TASK_STATE
# Initiating logger
logging = logging.getLogger(__name__)

# >>> ADD TASK STATE PROMPTS >>>
async def prompt_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_chat.id
    message_to_edit_id = query.message.message_id
    subtask_markup = subtasks_keyboard()

    try:
        await context.bot.edit_message_text(
            chat_id = user_id,
            message_id = message_to_edit_id,
            text = "You can send your \"task\" followed by a \":\" and then its \"priority\" "
            "(or urgency) as an integer from 1 to 3. You can always (from anywhere in the bot) use " \
            "the /add_task command followed by the same instructions to add your task.\n " \
            "Example: /add_task Go shopping:2",
            reply_markup = subtask_markup
        )
    except Exception as e:
        logging.info(f"An unknown exception arose: {e}")
    else:
        context.user_data['edited_main_menu_id'] = message_to_edit_id
        logging.info(f"Main menu with the ID {message_to_edit_id} was edited into a add_task_prompt.")

    return PROMPT_REMOVE_TASK_STATE


async def recieve_new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text

    if user_input.startswith('/'):
        new_task = user_input.strip('/add_task ').split(":")
    elif ":" in user_input:
        new_task = user_input.split(":")
    else:
        await context.bot.send_message(chat_id=user_id, text="Invalid format for adding a task.")
        return PROMPT_REMOVE_TASK_STATE
    
    user_at_hand = User(user_id)
    result = user_at_hand.add_user_task(task = new_task[0], priority=int(new_task[1]))

    if result == 0:
        logging.info(f"Task {new_task[0]} for user {user_id}, was addded successfully.")
        tasks_markup = tasks_keyboard()
        if context.user_data.get('edited_main_menu_id', None):
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = context.user_data.get('edited_main_menu_id'),
                text = f"Your task was successfully added✅\nYour tasks:\n{"\n".join(user_at_hand.get_user_tasks())}",
                reply_markup = tasks_markup
            )

            del user_at_hand
            return ConversationHandler.END
        else:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=context.user_data.get('main_menu_message_id'))
            except Exception as e:
                logging.info(f"{e}: An unimportant exception arose, trying to log tasks after adding one.")
            else:
                sent_message = await context.bot.send_message(
                    chat_id = user_id,
                    text = f"Your task was successfully added✅\nYour tasks:\n{"\n".join(user_at_hand.get_user_tasks())}",
                    reply_markup = tasks_markup
                )

                context.user_data['edited_main_menu_id'] = sent_message.message_id
                logging.info(f"A new edited main menu with ID {sent_message.message_id} was logged.")

                del user_at_hand
                return ConversationHandler.END
    else:
        await context.bot.send_message(chat_id=user_id, text="Something went wrong, try again!")
        return PROMPT_REMOVE_TASK_STATE
# <<< ADD TASK STATE PROMPTS <<<

def get_prompt_add_task_handler():
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^tasks_add$', callback=prompt_add_task),
            CommandHandler('add_task', recieve_new_task)
        ],
        states = {
            PROMPT_REMOVE_TASK_STATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recieve_new_task),
                CallbackQueryHandler(pattern='^subtasks_return$', callback=return_to_tasks)
            ]
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END : VIEW_TASKS_STATE
        },
        allow_reentry = True,
    )