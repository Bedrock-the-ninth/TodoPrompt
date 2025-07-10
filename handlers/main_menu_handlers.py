# handlers/main_menu_handlers.py
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
    filters, 
    MessageHandler   
)
from telegram.error import BadRequest, Forbidden
from inline_keyboards_module import main_menu_keyboard

import logging

logging = logging.getLogger(__name__)

VIEW_MENU = 0
VIEW_PROF_STATE = 1
VIEW_TASKS_STATE = 2
VIEW_REMINDERS_STATE = 3
VIEW_SETTING_STATE = 4


# >>> Main Menu >>>
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def close_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    query = update.callback_query
    await query.answer()

    prior_main_menu = context.user_data.get('main_menu_message_id')
    
    user_id = update.effective_chat.id
    message_to_edit_id = query.message.message_id

    main_menu_markup = main_menu_keyboard()

    if prior_main_menu == message_to_edit_id:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id = user_id,
                message_id = message_to_edit_id,
                reply_markup = main_menu_markup
            )

        except Forbidden:
            logging.info(f"The bot is blocked by the user {user_id}.")

        else:
            await context.bot.edit_message_text(
                chat_id = user_id, 
                message_id = message_to_edit_id, 
                text = "Here's the main menu:"
            )
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
                text = "Here's the main menu:"
            )
            await context.bot.edit_message_reply_markup(
                chat_id = user_id,
                message_id = message_to_edit_id,
                reply_markup = main_menu_markup
            )

    return VIEW_MENU


def get_main_menu_handler() -> CommandHandler:
    return ConversationHandler(
        entry_points = [CommandHandler('menu', main_menu)],
        states = {
            VIEW_MENU : [
                CallbackQueryHandler(pattern='^menu_view_profile$', callback=view_profile),
                CallbackQueryHandler(pattern='^menu_view_tasks$', callback=view_tasks),
                CallbackQueryHandler(pattern='^menu_view_reminders$', callback=view_reminders),
                CallbackQueryHandler(pattern='^menu_settings', callback=view_settings)
            ],
            VIEW_PROF_STATE : [
                CallbackQueryHandler(pattern='^profile_return$', callback=return_to_menu)
            ],
            VIEW_TASKS_STATE : [
                CallbackQueryHandler(pattern='^tasks_add$', callback=add_tasks),
                CallbackQueryHandler(pattern='^tasks_remove$', callback=remove_tasks),
                CallbackQueryHandler(pattern='^tasks_return', callback=return_to_menu)
            ],
            VIEW_REMINDERS_STATE : [
                CallbackQueryHandler(pattern='^reminders_achievement$', callback=achievement_reminders),
                CallbackQueryHandler(pattern='^reminders_last_call$', callback=last_call_reminders),
                CallbackQueryHandler(pattern='^reminders_return$', callback=return_to_menu)
            ],
            VIEW_SETTING_STATE : [
                CallbackQueryHandler(pattern='^settings_change_timezone$', callback=change_timezone),
                CallbackQueryHandler(pattern='^settings_remove_reminder_a$', callback=reminder_a_removal),
                CallbackQueryHandler(pattern='^settings_remove_reminder_l$', callback=reminder_l_removal),
                CallbackQueryHandler(pattern='^settings_delete_account$', callback=delete_account),
                CallbackQueryHandler(pattern='^settings_return&', callback=return_to_menu),
            ]
        },
        fallbacks = [
            CallbackQueryHandler(pattern='^menu_close$', callback=close_menu)
        ],
        allow_reentry = True
    )
# <<< Main Menu <<<