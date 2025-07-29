# /handlers/tasks/prompt_add_task_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
    filters, 
    MessageHandler   
)
# LOCAL imports ->
from config import VIEW_TASKS_STATE, PROMPT_ADD_TASK_STATE
from handlers.common.common_handlers import (
    close_all_convos, 
    return_to_tasks,
    delete_previous_menu,
    send_new_menu,
    edit_previous_menu
)
from handlers.common.inline_keyboard_handlers import tasks_keyboard, subtasks_keyboard
from helpers.user_data_util_classes.user_module import User

# Initiating logger
logger = logging.getLogger(__name__)


async def recieve_new_task_via_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text

    user_at_hand = User(user_id)

    await delete_previous_menu(update, context)

    if not user_at_hand._is_a_user:
        text = "You have not registered your timezone! You can do so tapping the /start command."

        await send_new_menu(update, context, text, None)
        raise ApplicationHandlerStop(ConversationHandler.END)
    else:
        # InlineKeyboardMarkup ->
        tasks_markup = tasks_keyboard()
        subtask_markup = subtasks_keyboard()

        if user_input.startswith('/'):
            new_task = user_input.strip('/add_task ').split(":")
        else:
            new_task = None

        if new_task != None:
            result = user_at_hand.task.add_user_task(task = new_task[0], priority=int(new_task[1]))
        else:
            result = 1

        if result != 0:
            error_text_1 = "Invalid input. Try again!"
            await send_new_menu(update, context, error_text_1, subtask_markup)
            

        else:
            logger.info(f"Task {new_task[0]} for user {user_id}, was addded successfully.")
            user_tasks = user_at_hand.task.get_user_tasks()
            user_tasks_string = "\n".join(user_tasks) if user_tasks else "---NO TASKS ADDED YET---"
            success_text_1 = f"Your task was successfully added✅\nYour tasks:\n{user_tasks_string}"
            
            await send_new_menu(update, context, success_text_1, tasks_markup)

        del user_at_hand
        return ConversationHandler.END

async def recieve_new_task_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text
    # InlineKeyboardMarkup ->
    tasks_markup = tasks_keyboard()
    subtask_markup = subtasks_keyboard()

    if ":" in user_input:
        new_task = user_input.split(":")
    else:
        new_task = None
    
    if new_task != None:
        user_at_hand = User(user_id)
        result = user_at_hand.task.add_user_task(task = new_task[0], priority=int(new_task[1]))
    else:
        result = 1

    if result != 0:
        error_text_1 = "Invalid input. Try again!"
        await edit_previous_menu(update, context, error_text_1, subtask_markup)

        del user_at_hand
        return PROMPT_ADD_TASK_STATE
    else:
        logger.info(f"Task {new_task[0]} for user {user_id}, was addded successfully.")
        user_tasks = user_at_hand.task.get_user_tasks()
        user_tasks_string = "\n".join(user_tasks) if user_tasks else "---NO TASKS ADDED YET---"
        success_text_1 = f"Your task was successfully added✅\nYour tasks:\n{user_tasks_string}"
        
        await edit_previous_menu(update, context, success_text_1, tasks_markup)

        del user_at_hand
        return ConversationHandler.END


# >>> ADD TASK STATE PROMPTS >>>
async def prompt_add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prior_main_menu = context.user_data['main_menu_message_id']
    message_to_edit_id = query.message.message_id

    add_task_guide_text = "You can send your \"task\" followed by a \":\" and then its \"priority\" (or urgency) as an integer from 1 to 3. You can always (from anywhere in the bot) use the /add_task command followed by the same instructions to add your task.\nExample: Go shopping:2\nor /add_task Go shopping:2"
    subtask_markup = subtasks_keyboard()

    if prior_main_menu == message_to_edit_id:
        await edit_previous_menu(update, context, add_task_guide_text, subtask_markup)
    else:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id
        await edit_previous_menu(update, context, add_task_guide_text, subtask_markup)

    return PROMPT_ADD_TASK_STATE
# <<< ADD TASK STATE PROMPTS <<<

def get_prompt_add_task_handler():
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^tasks_add$', callback=prompt_add_task),
            CommandHandler('add_task', recieve_new_task_via_command)
        ],
        states = {
            PROMPT_ADD_TASK_STATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recieve_new_task_via_text),
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