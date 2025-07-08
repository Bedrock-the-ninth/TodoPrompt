# IMPORTS #
# To load token ->
from dotenv import load_dotenv
from os import getenv
# To log when shit hits the fan ->
import logging
# Telegram Bot related imports ->
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder as AB, 
    CommandHandler as CH, 
    ContextTypes as CT, 
    ConversationHandler as ConvoH, 
    filters, 
    MessageHandler as MH, 
    JobQueue as JQ)
# Helper functions
import helpers

# State Definition for ConverstationHandlers
GET_TIMEZONE_STATE = 1

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    if not helpers.is_a_user(user_id):
        await context.bot.send_message(chat_id=user_id, text="Welcome to TaskPrompt! Please enter your timezone (e.g. UTC+3:30).")
        # Await users' timezone entery
        return GET_TIMEZONE_STATE
    else:
        await context.bot.sent_message(chat_id=user_id, text="What can I do for you today?")
        # Don't start the conversation of getting the timezone
        return ConvoH.END
    

async def get_timezone(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message

    if not helpers.validate_timezone(user_input):
        await context.bot.send_message(chat_id=user_id, text="That does not look like a valid UTC timezone. Use this format and try again (UTC+3:30).")
        return GET_TIMEZONE_STATE
    
    helpers.create_user_profile(user_id, user_input)
    logger.info(f"User {user_id} registered with timezone {user_input}")

    await context.bot.send_message(chat_id=user_id, text=f"Your timezone has been set to {user_input}. What can I do for you today?")

    return ConvoH.END


async def cancel(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    logging.info(f"User {user_id} cancelled the timezone setup.")

    await context.bot.send_message(chat_id=user_id, text="You have cancelled timezone setup. You can always restart by tapping /start.")

    return ConvoH.END


if __name__ == "__main__":
    # Load bot token from ./.env
    load_dotenv()
    TOKEN = getenv("BOT_TOKEN")
    # Initiate the DB
    helpers.db_initiator()
    
    application = AB().token(TOKEN).build()


    setup_convo_handler = ConvoH(
        entry_points=[CH('start', start)],
        states={
            GET_TIMEZONE_STATE: [MH(filters.TEXT & ~filters.COMMAND, get_timezone)],
        },
        fallbacks=[CH('cancel', cancel)],
        allow_reentry=True
    )


    application.add_handler(setup_convo_handler)
    
    application.run_polling()
    

