# handlers/settings/settings_handler.py

# GENERAL PYTHON imports ->

# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes, 
    ConversationHandler, 
)
from telegram.helpers import escape_markdown
# DOMESTIC imports ->
from config import VIEW_MENU, VIEW_SETTINGS
from handlers.common.common_handlers import return_to_menu, close_all_convos
from helpers.scheduler import unset_user_reminder


async def view_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def change_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def delete_d_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def delete_l_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

def get_settings_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern="^menu_settings$", callback=view_settings_menu)
        ],
        states = {
            VIEW_SETTINGS : [
                CallbackQueryHandler(pattern="^settings_change_timezone$", callback=change_timezone),
                CallbackQueryHandler(pattern="^settings_delete_d_reminder$", callback=delete_d_reminder),
                CallbackQueryHandler(pattern="^settings_delete_l_reminder$", callback=delete_l_reminder),
                CallbackQueryHandler(pattern="^settings_remove_account$", callback=remove_account),
                CallbackQueryHandler(pattern="^settings_return$", callback=return_to_menu)
            ]
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END: VIEW_MENU
        }
    )
