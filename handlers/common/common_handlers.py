# /handlers/common/common_handlers.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT IMPORTS
from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes, ConversationHandler
# LOCAL imports ->
from handlers.common.inline_keyboard_handlers import (
    main_menu_keyboard, 
    tasks_keyboard, 
    reminder_menu_keyboard
)
from helpers.user_data_util_classes.user_module import User

logger = logging.getLogger(__name__)


# THE HARDEST PILLS TO SWALLOW (also the rock of the whole project).
async def send_new_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str, markup: InlineKeyboardMarkup | None, parse_mode: ParseMode = None):
    user_id = update.effective_chat.id
    
    try:
        sent_message = await context.bot.send_message(
            chat_id = user_id,
            text = content,
            reply_markup = markup,
            parse_mode = parse_mode
        )
    except Exception as e:
        logger.error(f"{e}: An exception occured trying to send a new menu.")
    else:
        context.user_data['main_menu_message_id'] = sent_message.message_id
        logger.info(f"A new menu with ID {sent_message.message_id} was added.")


async def delete_previous_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    last_menu_message_id = context.user_data.get('main_menu_message_id', None)
    
    if last_menu_message_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=last_menu_message_id)
        except BadRequest:
            logger.error(f"Message {last_menu_message_id} in user{user_id}'s chat doesn't exist.")
        except Forbidden:
            logger.error(f"Message {last_menu_message_id} in user{user_id}'s isn't accessible.")
        except Exception as e:
            logger.error(f"An unknown error occured during the deletion of {last_menu_message_id} in user{user_id}'s chat.")
        else:
            logger.info(f"Message {last_menu_message_id} was successfully removed from user{user_id}'s chat.")


async def edit_previous_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, content: str | None, markup: InlineKeyboardMarkup | None, parse_mode: ParseMode = None):
    user_id = update.effective_chat.id
    to_be_edited_id = context.user_data.get('main_menu_message_id', None)

    if to_be_edited_id:
        try:
            await context.bot.edit_message_text(
                chat_id = user_id,
                message_id = to_be_edited_id,
                text = content,
                reply_markup = markup,
                parse_mode = parse_mode
            )
        except BadRequest:
            logger.error(f"Message {to_be_edited_id} in user{user_id}'s chat doesn't exist.")
        except Forbidden:
            logger.error(f"Message {to_be_edited_id} in user{user_id}'s isn't accessible.")
        except Exception as e:
            logger.error(f"An unknown error occured during the deletion of {to_be_edited_id} in user{user_id}'s chat.")
        else:
            logger.info(f"Message {to_be_edited_id} was successfully edited in user{user_id}'s chat.")
# THE HARDESTS PILLS HAVE BEEN SWALLOWED.

async def close_all_convos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    This handler, closes all open menus and windows, and ends the main menu
    conversation flow and cycle. (To be extended later on.)
    """    
    # Delete last logged main menu:
    await delete_previous_menu(update, context)
    
    # Send a confirmation message
    text="Operation cancelled. All active flows and menus have been closed."
    await send_new_menu(update, context, text, None)

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
    message_to_edit_id = query.message.message_id

    main_menu_markup = main_menu_keyboard()
    text = "Here's the main menu:"

    if prior_main_menu == message_to_edit_id:
        await edit_previous_menu(update, context, text, main_menu_markup)
    else:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id
        await edit_previous_menu(update, context, text, main_menu_markup)

    return ConversationHandler.END


async def return_to_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    message_to_edit_id = query.message.message_id
    prior_main_menu = context.user_data['main_menu_message_id']

    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    if prior_main_menu != message_to_edit_id:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id

    # Setup for editing the task menu
    no_task_text = "No tasks are added yet. Try adding one by touching the button \"➕ Add\"" \
    "or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2"

    user_tasks = user_at_hand.task.get_user_tasks()
    tasks_markup = tasks_keyboard()

    if not user_tasks:
        user_tasks_string = "\n".join("--NO TASKS ADDED YET--")
        await edit_previous_menu(update, context, f"Tasks:\n{user_tasks_string}", tasks_markup)
    else:
        user_tasks_string = "\n".join(user_tasks)
        await edit_previous_menu(update, context, f"Tasks:\n{user_tasks_string}", tasks_markup)
    
    del user_at_hand
    return ConversationHandler.END


async def return_to_reminders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    message_to_edit_id = query.message.message_id
    prior_main_menu = context.user_data['main_menu_message_id']

    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    reminders = user_at_hand.reminder
    info = user_at_hand._info

    if prior_main_menu != message_to_edit_id:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id

    # Setup for editing the task menu
    no_instance_text = "No reminders set just yet! You can navigate this menue " \
    "(also accessible through /reminders command) to set new ones or go to settings" \
    " (or /settings) to remove the once you've set some.  O.O\n"
    some_instances_text = "You've set the following reminders:\n"

    reminder_done_state = reminders.check_reminder_state('DONE', 1)
    reminder_left_state = reminders.check_reminder_state('LEFT', 1)

    flag = 0
    if (reminder_done_state != 0) and (reminder_left_state != 0):
        no_instance_text += "\n".join("--NO REMINDERS ADDED YET--")
        flag = 1
    elif (reminder_done_state == 0) and (reminder_left_state != 0):
        some_instances_text += f"⌚ Achievement Reminder Is Set For: {info.get('reminder_done')}"
    elif (reminder_done_state != 0) and (reminder_left_state == 0):
        some_instances_text += f"⌛ Last Call Reminder Is Set For: {info['reminder_left']}"
    else:
        some_instances_text += f"⌚ Achievement Reminder Is Set For: {info.get('reminder_done', None)}\n ⌛ Last Call Reminder Is Set For: {info['reminder_left']}"

    reminder_markup = reminder_menu_keyboard()

    if flag == 1:
        await edit_previous_menu(update, context, no_instance_text, reminder_markup)
    else:
        await edit_previous_menu(update, context, some_instances_text, reminder_markup)
    
    del user_at_hand
    return ConversationHandler.END
