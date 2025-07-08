# IMPORTS #
# To load token ->
from dotenv import load_dotenv
from os import getenv
# To log when shit hits the fan ->
import logging
# Telegram Bot related imports ->
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder as AB, CommandHandler as CH, ContextTypes as CT, JobQueue as JQ


async def start(update: Update, context: CT.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter your timezone (e.g. UTC+3:30):")


if __name__ == "__main__":
    # Load bot token from ./.env
    load_dotenv()
    TOKEN = getenv("BOT_TOKEN")    
    
    application = AB().token(TOKEN).build()
    
    start_handler = CH('start', start)
    application.add_handler(start_handler)
    
    application.run_polling()
    

