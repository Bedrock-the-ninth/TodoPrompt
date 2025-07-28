# /handlers/tasks/prompt_check_task_handler.py

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
from config import VIEW_TASKS_STATE, PROMPT_CHECK_TASK_STATE
from handlers.common.common_handlers import (
    close_all_convos, 
    return_to_tasks,
    delete_previous_menu,
    send_new_menu,
    edit_previous_menu
)
from handlers.common.inline_keyboards_module import tasks_keyboard, subtasks_keyboard
from helpers.user_data_util_classes.user_class import User

# Initiating logger
logger = logging.getLogger(__name__)



async def mark_task_done(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int, row_number: str, query_type: str):
    user_id = uid
    user_input = row_number

    # Getting user_tasks list 
    user_at_hand = User(user_id)
    user_task_list = user_at_hand.task.get_user_tasks()
    if user_task_list:
        user_tasks = "Your tasks are as follows:\n" + ("\n".join(user_task_list))
    else:
        user_tasks = "\n".join("---NO TASKS ADDED YET---")

    tasks_markup = tasks_keyboard()

    try:
        user_input = int(user_input) - 1
    except (ValueError, TypeError):
        error_text_1 = "❌Failed: Input was not an integer.\n"
        
        logger.info(error_text_1)
        if query_type == "text":
            await edit_previous_menu(update=update, context=context, content=(error_text_1 + user_tasks), markup=tasks_markup)
        elif query_type == "command":
            await delete_previous_menu(update, context)
            await send_new_menu(update, context, content=(error_text_1 + user_tasks), markup=tasks_markup)
        return PROMPT_CHECK_TASK_STATE
    else:
        if not (0 <= user_input < len(user_task_list)):
            error_text_2 = "❌Failed: The integer user entered is out of range.\n"

            logger.info(error_text_2)
            if query_type == "text":
                await edit_previous_menu(update=update, context=context, content=(error_text_2 + user_tasks), markup=tasks_markup)
            elif query_type == "command":
                await delete_previous_menu(update, context)
                await send_new_menu(update, context, content=(error_text_2 + user_tasks), markup=tasks_markup)
            return PROMPT_CHECK_TASK_STATE
        
        else:
            task_to_be_marked_string : str = user_task_list[user_input]
            task_to_be_marked = task_to_be_marked_string.split('--')[1].strip()

            results = user_at_hand.task.mark_done_and_return_new_list(task_to_be_marked)

            if results is None:
                error_text_3 = "❌Failed: Updating the database failed.\n"

                logger.info(error_text_3)
                if query_type == "text":
                    await edit_previous_menu(update=update, context=context, content=(error_text_3 + user_tasks), markup=tasks_markup)
                elif query_type == "command":
                    await delete_previous_menu(update, context)
                    await send_new_menu(update, context, content=(error_text_3 + user_tasks), markup=tasks_markup)
                return PROMPT_CHECK_TASK_STATE
            
            elif results == 1:
                error_text_4 = "❌Failed: Couldn't retreive the tasklist.\n"

                logger.info(error_text_4)
                if query_type == "text":
                    await edit_previous_menu(update=update, context=context, content=(error_text_4 + user_tasks), markup=tasks_markup)
                elif query_type == "command":
                    await delete_previous_menu(update, context)
                    await send_new_menu(update, context, content=(error_text_4 + user_tasks), markup=tasks_markup)
                return PROMPT_CHECK_TASK_STATE
            
            else:
                success_text = "^_-  Success: Task was marked done."
                results = f"Tasks:\n" + ("\n".join(results))
                logger.info(success_text)
                if query_type == "text":
                    await edit_previous_menu(update=update, context=context, content=(success_text + results), markup=tasks_markup)
                elif query_type == "command":
                    await delete_previous_menu(update, context)
                    await send_new_menu(update, context, content=(success_text + results), markup=tasks_markup)
                return ConversationHandler.END

async def mark_done_via_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text
    # InlineKeyboardMarkup ->
    subtasks_markup = subtasks_keyboard()
    # User instantiation

    user_at_hand = User(user_id)

    await delete_previous_menu(update, context)

    if not user_at_hand._is_a_user:
        text = "You have not registered your timezone! You can do so tapping the /start command."

        await send_new_menu(update, context, text, None)
        raise ApplicationHandlerStop(ConversationHandler.END)
    else:
        if user_input.startswith('/'):
            user_input = user_input.replace('/mark_done ', "").strip()
            await mark_task_done(update, context, user_id, user_input, "command")
        else:
            error_text_1 = "U_U  An error occured while marking your task done. Try again! Your tasks: \n"

            user_tasks_list = user_at_hand.task.get_user_tasks()
            if user_tasks_list:
                user_tasks = "\n".join(user_tasks_list)
            else:
                user_tasks = "\n".join("--NO TASKS ADDED YET--")

            await send_new_menu(update, context, content=(error_text_1 + user_tasks), markup=subtasks_markup)
            
            del user_at_hand
            return PROMPT_CHECK_TASK_STATE

async def mark_done_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text
    # InlineKeyboardMarkup ->
    subtasks_markup = subtasks_keyboard()
    # User instantiation

    user_input = user_input.strip()
    await mark_task_done(update, context, user_id, user_input, "text")
        


# >>> CHECK TASK STATE PROMPTS >>>
async def prompt_check_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prior_main_menu = context.user_data['main_menu_message_id']
    message_to_edit_id = query.message.message_id

    add_task_guide_text = "(～￣▽￣)～  Mark your tasks done by sending their row number, right here!\nOr you can use /mark_done <row number> anywhere in the bot."
    subtask_markup = subtasks_keyboard()

    if prior_main_menu == message_to_edit_id:
        await edit_previous_menu(update, context, add_task_guide_text, subtask_markup)
    else:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id
        await edit_previous_menu(update, context, add_task_guide_text, subtask_markup)

    return PROMPT_CHECK_TASK_STATE
# <<< CHECK TASK STATE PROMPTS <<<

def get_prompt_check_task_handler():
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^tasks_check$', callback=prompt_check_task),
            CommandHandler('mark_done', mark_done_via_command)
        ],
        states = {
            PROMPT_CHECK_TASK_STATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mark_done_via_text),
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