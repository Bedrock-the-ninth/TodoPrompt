# handlers/settings/settings_handler.py

# GENERAL PYTHON imports ->
import logging
from asyncio import sleep
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes, 
    ConversationHandler, 
    filters,
    MessageHandler
)
from telegram.helpers import escape_markdown
# DOMESTIC imports ->
from config import VIEW_MENU, VIEW_SETTINGS, RESET_TIMEZONE
from handlers.common.common_handlers import (
    send_new_menu,
    delete_previous_menu,
    edit_previous_menu,
    return_to_menu, 
    close_all_convos
)
from handlers.common.inline_keyboards_module import settings_keyboard, sub_settings_keyboard
from helpers.scheduler import unset_user_reminder
from helpers.user_data_utils import User

logger = logging.getLogger(__name__)


async def view_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = escape_markdown("⚙️*Here's the settings menu:*", version=2)
    settings_markup = settings_keyboard()
    parse_mode = ParseMode.MARKDOWN_V2 # Define parse_mode once

    if update.callback_query:
        query = update.callback_query
        await query.answer() 
        await edit_previous_menu(update, context, text, settings_markup, parse_mode=parse_mode)
    elif update.message and update.message.text.startswith('/settings'):
        await send_new_menu(update, context, text, settings_markup, parse_mode=parse_mode)
    else:
        logger.warning(f"view_settings_menu called with unhandled update type for user {update.effective_chat.id}")
        await send_new_menu(update, context, text, settings_markup, parse_mode=parse_mode)

    return VIEW_SETTINGS


async def reset_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    user_input = update.message.text
    parse_mode = ParseMode.MARKDOWN_V2

    if not user_at_hand.is_timezone_valid(user_input):
        text = escape_markdown("Doens't look like a valid IANA timezone. You could search for country's IANA and retry.", version=2)
        sub_settings_markup = sub_settings_keyboard()
        await edit_previous_menu(update, context, text, sub_settings_markup, parse_mode)
        return RESET_TIMEZONE

    user_at_hand.create_user_profile(user_input)
    logger.info(f"User {user_id} reset timezone into {user_input}")

    success_text = escape_markdown(f"Your timezone has been set to {user_input}. Tap /menu or use the return button to use my functionalities.", version=2)
    settings_markup = settings_keyboard()
    await edit_previous_menu(update, context, success_text, settings_markup, parse_mode)
    return VIEW_SETTINGS


async def change_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = escape_markdown("To reset or override the previously input timezone, send your IANA timezone again (e.g. \"Asia/Tehran\" or \"Europe/Berlin\").", version=2)
    sub_settings_markup = sub_settings_keyboard()

    await edit_previous_menu(update, context, text, sub_settings_markup, ParseMode.MARKDOWN_V2)
    return RESET_TIMEZONE


async def delete_d_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    removing_reminder_result = await unset_user_reminder(update, context, "DONE")

    if removing_reminder_result[0] != 0:
        text = "Achievement Reminder was not successfully removed!❌ \n⚙️Back to settings menu..."
    else:
        text = "Achievemnt Reminder was successfully removed!✅ \n⚙️Back to settings menu..."
    settings_markup = settings_keyboard()

    await edit_previous_menu(update, context, text, settings_markup, ParseMode.MARKDOWN_V2)
    return VIEW_SETTINGS

async def delete_l_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    removing_reminder_result = await unset_user_reminder(update, context, "LEFT")
    
    if removing_reminder_result[0] != 0:
        text = "Last Call Reminder was not successfully removed!❌ \n⚙️Back to settings menu..."
    else:
        text = "Last Call Reminder was successfully removed!✅ \n⚙️Back to settings menu..."
    settings_markup = settings_keyboard()

    await edit_previous_menu(update, context, text, settings_markup, ParseMode.MARKDOWN_V2)
    return VIEW_SETTINGS


async def remove_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    # Database info removal:
    user_at_hand.delete_user_profile()

    # JobSchedule and Reminders removal
    await unset_user_reminder(update, context, "DONE")
    await unset_user_reminder(update, context, "LEFT")

    # Final Interaction:
    text = escape_markdown("You are now stir clear of me. *_Goodbye friend!_*🥲\nIt would be a good idea to clear our history and then /start the chat again, just in case.", version=2)
    await delete_previous_menu(update, context)
    await send_new_menu(update, context, text, None, ParseMode.MARKDOWN_V2)

    # PicklePersistence info removal
    context.user_data.clear()

    return ConversationHandler.END

def get_settings_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points = [
            CommandHandler('settings', view_settings_menu),
            CallbackQueryHandler(pattern="^menu_settings$", callback=view_settings_menu)
        ],
        states = {
            VIEW_SETTINGS : [
                CallbackQueryHandler(pattern="^settings_change_timezone$", callback=change_timezone),
                CallbackQueryHandler(pattern="^settings_delete_d_reminder$", callback=delete_d_reminder),
                CallbackQueryHandler(pattern="^settings_delete_l_reminder$", callback=delete_l_reminder),
                CallbackQueryHandler(pattern="^settings_remove_account$", callback=remove_account),
                CallbackQueryHandler(pattern="^settings_return$", callback=return_to_menu)
            ],
            RESET_TIMEZONE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reset_timezone),
                CallbackQueryHandler(pattern="^sub_settings_return$", callback=view_settings_menu)
            ]
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END: VIEW_MENU
        }
    )
