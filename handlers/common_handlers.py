from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest, Forbidden
import logging
from helpers.user_data_utils import User
from handlers.inline_keyboards_module import main_menu_keyboard, tasks_keyboard
from config import VIEW_MENU

logging = logging.getLogger(__name__)


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