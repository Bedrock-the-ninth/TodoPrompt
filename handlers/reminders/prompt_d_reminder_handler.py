# /handlers/reminders/prompt_d_reminder_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes, 
    ConversationHandler,
    MessageHandler,
    filters
)
# LOCAL imports
from config import VIEW_REMINDERS_STATE, PROMPT_D_REMINDER_STATE
from handlers.common.inline_keyboard_handlers import reminder_menu_keyboard, sub_reminder_keyboard
from handlers.common.common_handlers import (
    close_all_convos,
    delete_previous_menu,
    edit_previous_menu,
    return_to_reminders_menu,
)
from helpers.scheduler.scheduler import set_user_reminder

logger = logging.getLogger(__name__)


async def view_done_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prior_main_menu = context.user_data.get('main_menu_message_id', None)
    message_to_edit_id = query.message.message_id
    main_text = "You can send a time to recieve your Achievement Reminder on that given time. " \
    "The input must be in the 24 hours format (e.g. 17:00). Achievement Reminders are only to bring the tasks " \
    "that were marked done to your attention and probably boost your confidence  []~(￣▽￣)~*. If there is " \
    "any Achievement Reminders set, sending a new time would override the old one."
    sub_reminder_markup = sub_reminder_keyboard()

    if message_to_edit_id == prior_main_menu:
        pass
    else:
        await delete_previous_menu(update, context)
        context.user_data['main_menu_message_id'] = message_to_edit_id
        
    await edit_previous_menu(update, context, main_text, sub_reminder_markup)
    return PROMPT_D_REMINDER_STATE


async def add_done_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text
    sub_reminder_markup = sub_reminder_keyboard()

    try:
        input_hour, input_minute = map(int, user_input.split(":"))
    except (ValueError, TypeError):
        logger.error(f"User {user_id}, input value in wrong format.")
        await edit_previous_menu(update, context, "Unacceptable formatted input. Try again!", sub_reminder_markup)
        return PROMPT_D_REMINDER_STATE
    else:
        result = await set_user_reminder(update, context, "DONE")
        
        if result[0] == 1:
            await edit_previous_menu(update, context, "An error occured scheduling the job. Try again!", sub_reminder_keyboard)
            return PROMPT_D_REMINDER_STATE
        elif result[0] == 0:
            reminder_menu_markup = reminder_menu_keyboard()
            await edit_previous_menu(update, context, f"Scheduled a new Achievement Reminder for {result[2]}.", reminder_menu_markup)
            return ConversationHandler.END


def get_prompt_d_reminder_handler():
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern="^reminders_add_d_reminder$", callback=view_done_reminder),
        ],
        states = {
            PROMPT_D_REMINDER_STATE : [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_done_reminder),
                CallbackQueryHandler(pattern="^sub_reminder_return$", callback=return_to_reminders_menu)
            ]
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END : VIEW_REMINDERS_STATE
        },
        allow_reentry = True
    )