# handlers/reminders_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes, 
    ConversationHandler,
)
# DOMESTIC imports
from config import (
    VIEW_MENU, 
    VIEW_REMINDERS_STATE, 
)
from handlers.common.inline_keyboards_module import reminder_menu_keyboard
from handlers.common.common_handlers import (
    delete_previous_menu,
    send_new_menu,
    return_to_menu,
    close_all_convos
)
from helpers.user_data_utils import User

logger = logging.getLogger(__name__)


async def view_reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    info = user_at_hand.info

    # Setup for editing the reminders menu
    no_instance_text = "No reminders set just yet! You can navigate this menue " \
    "(also accessible through /reminders command) to set new ones or go to settings" \
    " (or /settings) to remove the once you've set some.  O.O\n"
    some_instances_text = "You've set the following reminders:\n"

    flag = 0
    if (info['reminder_done'] is None) and (info['reminder_left'] is None):
        no_instance_text += "\n".join("--NO REMINDERS ADDED YET--")
        flag = 1
    elif (type(info['reminder_done']) is str) and (info['reminder_left'] is None):
        some_instances_text += f"⌚ Achievement Reminder Is Set For: {info['reminder_done']}"
    elif (info['reminder_done'] is None) and (type(info['reminder_left']) is str):
        some_instances_text += f"⌛ Last Call Reminder Is Set For: {info['reminder_left']}"
    else:
        some_instances_text += f"⌚ Achievement Reminder Is Set For: {info['reminder_done']}\n ⌛ Last Call Reminder Is Set For: {info['reminder_left']}"

    reminder_markup = reminder_menu_keyboard()

    await delete_previous_menu(update, context)
    if flag == 1:
        await send_new_menu(update, context, no_instance_text, reminder_markup)
    else:
        await send_new_menu(update, context, some_instances_text, reminder_markup)
    
    del user_at_hand
    return VIEW_REMINDERS_STATE

async def add_left_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

def get_reminders_menu_handler():
    return ConversationHandler(
        entry_points = [
            CommandHandler('reminders', view_reminder_menu),
            CallbackQueryHandler(pattern="^menu_view_reminders$", callback=view_reminder_menu),
        ],
        states = {
            VIEW_REMINDERS_STATE : [
                CallbackQueryHandler(pattern="^reminders_return$", callback=return_to_menu)
            ]
        },
        map_to_parent = {
            ConversationHandler.END : VIEW_MENU
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        allow_reentry = True
    )