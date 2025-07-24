# handlers/start_conversation_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)
# DOMESTIC imports ->
from helpers.user_data_utils import User
# STATE imports ->
from config import GET_TIMEZONE_STATE

# To use logger:
logger = logging.getLogger(__name__)


# >>> User timezone setup >>>
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)

    if not user_at_hand._is_a_user:
        await context.bot.send_message(chat_id=user_id,
                                       text="Welcome to TaskPrompt! Please enter your IANA timezone (e.g. \"Asia/Tehran\" or \"Europe/Berlin\").")
        return GET_TIMEZONE_STATE
    else:
        await context.bot.send_message(chat_id=user_id, text="Tap /menu to use my functionalities.")

        return ConversationHandler.END


async def get_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_at_hand = User(user_id)
    user_input = update.message.text

    if not user_at_hand.is_timezone_valid(user_input):
        await context.bot.send_message(chat_id=user_id,
                                       text="Doens't look like a valid IANA timezone. You could search for country's IANA and retry.")
        return GET_TIMEZONE_STATE

    user_at_hand.create_user_profile(user_id, user_input)
    logger.info(f"User {user_id} registered with timezone {user_input}")

    await context.bot.send_message(chat_id=user_id, text=f"Your timezone has been set to {user_input}. Tap /menu to use my functionalities.")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    logger.info(f"User {user_id} cancelled the timezone setup.")
    await context.bot.send_message(chat_id=user_id,
                                   text="You have cancelled timezone setup. You can always restart by tapping /start.")
    return ConversationHandler.END


# Returning the startup conversation as a ConversationHandler Object:
def get_setup_conversation_handler() -> ConversationHandler:
    """Returns the ConversationHandler for the initial timezone setup."""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_TIMEZONE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_timezone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )