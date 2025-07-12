# handlers/task_menu_handler.py

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
from handlers.inline_keyboards_module import tasks_keyboard
from handlers.prompt_add_task_handler import prompt_add_task
from handlers.main_menu_handlers import return_to_menu, close_all_convos
from helpers.user_data_utils import User

# State Definition for ConversationHandlers
from config import VIEW_MENU, VIEW_TASKS_STATE
# Initiating logger
logging = logging.getLogger(__name__)


# >>> Task Menu >>>
async def view_task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user info and tasks
    user_id = update.effective_CommandHandlerat.id
    user_at_hand = User(user_id)
    user_tasks = "\n".join(user_at_hand.get_user_tasks())
    # Setting up keyboard markup
    tasks_markup = tasks_keyboard()

    # Get the message id for the previous menu
    if update.callback_query:

        query = update.callback_query
        await query.answer()
        message_to_edit_id = query.message.message_id

        if user_tasks[0] == 1:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = message_to_edit_id,
                text = "No tasks are added yet. Try adding one by touching the button \"➕ Add\" "
                "or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2",
                reply_markup = tasks_markup
            )
        else:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = message_to_edit_id,
                text = f"Tasks:\n{user_tasks}",
                reply_markup = tasks_markup
            )
        context.user_data['main_menu_message_id'] = message_to_edit_id
        logging.info(f"A new main menu with ID {context.user_data.get('main_menu_message_id')} was add.")
        
    elif update.message and update.message.text.startswith('/'):

        await context.bot.delete_message(chat_id=user_id, message_id=context.user_data.get('main_menu_message_id'))
        logging.info(f"Main menu with ID {context.user_data.get('main_menu_message_id')} was removed.")

        if user_tasks[0] == 1:
            sent_message = await context.bot.send_message(
                chat_id = user_id,
                text = "No tasks are added yet. Try adding one by touching the button \"➕ Add\""
                " or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2",
                reply_markup = tasks_markup
            )

            context.user_data['main_menu_message_id'] = sent_message.message_id
            logging.info(f"A new main menu with ID {context.user_data.get('main_menu_message_id')} was added.")
        else:
            sent_message = await context.bot.send_message(
                chat_id = user_id,
                text = f"Tasks:\n{user_tasks}",
                reply_markup = tasks_markup
            )

            context.user_data['main_menu_message_id'] = sent_message.message_id
            logging.info(f"A new main menu with ID {context.user_data.get('main_menu_message_id')} was added.")
    
    del user_at_hand

    return VIEW_TASKS_STATE


def get_task_menu_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^menu_view_tasks$', callback=view_task_menu),
            CommandHandler('tasks', view_task_menu)
        ],
        states = {
            VIEW_TASKS_STATE : [
                CallbackQueryHandler(pattern='^tasks_add$', callback=prompt_add_task),
                CallbackQueryHandler(pattern='^tasks_remove$', callback=prompt_remove_task),
                CallbackQueryHandler(pattern='^tasks_return$', callback=return_to_menu)
            ],
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END : VIEW_MENU
        },
        allow_reentry = True
    )
# <<< Task Menu <<<
