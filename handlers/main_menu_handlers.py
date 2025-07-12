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
from handlers.task_menu_handlers import view_task_menu
from helpers.user_data_utils import User
from inline_keyboards_module import main_menu_keyboard, profile_menu_keyboard
# STATE imports ->
from config import VIEW_MENU, VIEW_PROF_STATE


logging = logging.getLogger(__name__)


async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This is a button handler for the close button in the main menu.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_chat.id
    message_to_edit_id = query.message.message_id

    try:
        await context.bot.edit_message_reply_markup(
            chat_id = user_id,
            message_id = message_to_edit_id,
            reply_markup = None
        )

    except Forbidden:
        logging.info(f"The bot is blocked by the user {user_id}.")

    else:
        await context.bot.edit_message_text(
            chat_id = user_id, 
            message_id = message_to_edit_id, 
            text = "Menu was closed ❌\nYou can reopen it using the command /menu."
        )
        
        if context.user_data.get('main_menu_message_id') == message_to_edit_id:
            e = context.user_data.pop('main_menu_message_id', None)
            logging.info(f"{e}: Main menu was closed and removed from user_data.")

    return ConversationHandler.END


async def return_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, belongs to return buttons beneath parts which are in
    reach of the main menu with a return button.
    """
    query = update.callback_query
    await query.answer()

    prior_main_menu = context.user_data.get('main_menu_message_id')
    
    user_id = update.effective_chat.id
    message_to_edit_id = query.message.message_id

    main_menu_markup = main_menu_keyboard()

    if prior_main_menu == message_to_edit_id:
        try:
            await context.bot.edit_message_text(
                chat_id = user_id, 
                message_id = message_to_edit_id, 
                text = "Here's the main menu:",
                reply_markup = main_menu_markup
            )
        except Forbidden:
            logging.info(f"The bot is blocked by the user {user_id}.")
    else:
        try:
            await context.bot.delete_message(
                chat_id = user_id,
                message_id = prior_main_menu
            )

        except BadRequest:
            logging.info(f"User {user_id} had no access to {prior_main_menu} message.")

        except Forbidden:
            logging.info(f"The bot is blocked by the user {user_id}.")

        else:
            await context.bot.edit_message_text(
                chat_id = user_id, 
                message_id = message_to_edit_id, 
                text = "Here's the main menu:",
                reply_markup = main_menu_markup
            )

            context.user_data['main_menu_message_id'] = message_to_edit_id
            logging.info(f"Main menu with ID {message_to_edit_id} was added.")

    return VIEW_MENU


async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, retreives user data through helpers.User class
    and outputs a formatted string of information. Still a part
    of the main menu conversation.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_chat.id
    message_to_edit_id = query.message.message_id

    prior_main_menu = context.user_data.get('main_menu_message_id', None)
    user_at_hand = User(user_id)
    profile_menu_markup = profile_menu_keyboard()

    if prior_main_menu:
        try:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = message_to_edit_id,
                text = user_at_hand.get_user_profile(),
                reply_markup = profile_menu_markup
            )
        except Exception as e:
            logging.info(f"{e}: Some exceptions arouse")
        else:
            del user_at_hand
    
    context.user_data['main_menu_message_id'] = message_to_edit_id

    return VIEW_PROF_STATE


async def close_all_convos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, closes all open menus and windows, and ends the main menu
    conversation flow and cycle. (To be extended later on.)
    """
    user_id = update.effective_chat.id
    
    # Delete last logged main menu:
    prior_main_menu_id = context.user_data.get('main_menu_message_id')
    if prior_main_menu_id:
        try:
            await context.bot.delete_message(user_id, prior_main_menu_id)
            logging.info(f"Prior main menu message with ID {prior_main_menu_id} was successfully deleted by /cancel.")
            context.user_data.pop('main_menu_message_id', None) # Clear the stored ID
        except BadRequest:
            logging.info(f"User {user_id} had no access to {prior_main_menu_id} message.")
            context.user_data.pop('main_menu_message_id', None)
        except Forbidden:
            logging.info(f"The bot is blocked by the user {user_id}.")
            context.user_data.pop('main_menu_message_id', None)
        except Exception as e:
            logging.error(f"An unexpected error occurred trying to delete message {prior_main_menu_id} for user {user_id}")
    
    # Send a confirmation message
    await context.bot.send_message(chat_id=user_id, text="Operation cancelled. All active flows and menus have been closed.")

    # End the conversation cycle
    return ConversationHandler.END


# >>> Main Menu >>>
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, handles the main menu's appearance and behavior. 
    """

    user_id = update.effective_chat.id

    main_menu_markup = main_menu_keyboard()

    prior_main_menu = context.user_data.get('main_menu_message_id')
    if prior_main_menu:
        if prior_main_menu:
            try:
                await context.bot.delete_message(user_id, prior_main_menu)
            except BadRequest:
                logging.info(f"Message with ID {prior_main_menu} was not found")
                context.user_data.pop('main_menu_message_id')
            except Forbidden:
                logging.info(f"Bot was blocked by the user. DELETING MESSAGE ID")
                context.user_data.pop('main_menu_message_id')
            except Exception as e:
                logging.info(f"An unexpected error: {e}")
            else:
                logging.info(f"Main menu with this ID was removed: {prior_main_menu}")

    sent_message = await context.bot.send_message(
        chat_id = user_id, 
        text = "Here's the main menu:", 
        reply_markup = main_menu_markup
    )

    context.user_data['main_menu_message_id'] = sent_message.message_id
    logging.info(f"/main command main menu message ID was stored: {sent_message.message_id}")

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
                CallbackQueryHandler(pattern='^menu_view_tasks$', callback=view_task_menu),
                CallbackQueryHandler(pattern='^menu_view_reminders$', callback=view_reminders),
                CallbackQueryHandler(pattern='^menu_settings', callback=view_settings)
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