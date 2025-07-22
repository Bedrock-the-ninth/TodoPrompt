# handlers/main_menu_handlers.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
)
# DOMESTIC imports ->
from handlers.common.common_handlers import (
    close_all_convos, 
    return_to_menu, 
    delete_previous_menu, 
    send_new_menu, 
    edit_previous_menu
)
from helpers.user_data_utils import User
from handlers.common.inline_keyboards_module import main_menu_keyboard, profile_menu_keyboard
# STATE imports ->
from config import VIEW_MENU, VIEW_PROF_STATE


logger = logging.getLogger(__name__)


async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This is a button handler for the close button in the main menu.
    """
    query = update.callback_query
    await query.answer()
    
    context.user_data['main_menu_message_id'] = query.message.message_id
    text = "Menu was closed ❌\nYou can reopen it using the command /menu."

    await edit_previous_menu(update, context, text, None)

    return ConversationHandler.END


async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, retreives user data through helpers.User class
    and outputs a formatted string of information. Still a part
    of the main menu conversation.
    """
    query = update.callback_query
    await query.answer()

    context.user_data['main_menu_message_id'] = query.message.message_id

    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    user_profile = user_at_hand.get_user_profile()
    profile_menu_markup = profile_menu_keyboard()

    await edit_previous_menu(update, context, user_profile, profile_menu_markup)

    del user_at_hand
    return VIEW_PROF_STATE


# >>> Main Menu >>>
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, handles the main menu's appearance and behavior. 
    """

    text = "Here's the main menu:"
    main_menu_markup = main_menu_keyboard()

    await delete_previous_menu(update, context)
    await send_new_menu(update, context, text, main_menu_markup)

    return VIEW_MENU


def get_main_menu_handler() -> ConversationHandler:
    """
    Returning a ConversationHandler object back to the bot.py
    to be rendered in the application. 
    """
    return ConversationHandler(
        entry_points = [CommandHandler('menu', main_menu)],
        states = {
            VIEW_MENU : [
                CallbackQueryHandler(pattern='^menu_view_profile$', callback=view_profile),
                # CallbackQueryHandler(pattern='^menu_view_reminders$', callback=view_reminders),
                # CallbackQueryHandler(pattern='^menu_settings', callback=view_settings)
            ],
            VIEW_PROF_STATE : [
                CallbackQueryHandler(pattern='^profile_return$', callback=return_to_menu)
            ],
        },
        fallbacks = [
            CallbackQueryHandler(pattern='^menu_close$', callback=close_menu),
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END : ConversationHandler.END
        },
        allow_reentry = True,
    )
# <<< Main Menu <<<