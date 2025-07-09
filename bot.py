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
    CallbackQueryHandler as CQH,
    CommandHandler as CH,
    ContextTypes as CT,
    ConversationHandler as ConvoH,
    filters,
    JobQueue as JQ,
    MessageHandler as MH,
    PicklePersistence as PP)
# Helper functions
import helpers

# State Definition for ConversationHandlers
GET_TIMEZONE_STATE = 1

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


# >>> Inline Keyboard >>>
def make_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 View Your Profile.", callback_data="menu_view_profile")],
        [InlineKeyboardButton("📝 View Tasks", callback_data="menu_view_tasks"), InlineKeyboardButton("🔔 Set Reminders", callback_data="menu_add_tasks")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menue_settings"), InlineKeyboardButton("❌ Close Menue", callback_data="menue_settings")]
    ]

    return InlineKeyboardMarkup(keyboard)


def make_profile_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Return to Menu", callback_data="profile_return")]
    ]

    return InlineKeyboardMarkup(keyboard)


def make_tasks_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Add", callback_data="tasks_add"), InlineKeyboardButton("➖ Remove", callback_data="tasks_remove")]
        [InlineKeyboardButton("🔙 Return to Menu", callback_data="return_button")]
    ]

    return InlineKeyboardMarkup(keyboard)


def make_subtasks_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Return to Tasks", callback_data="subtasks_return")]
    ]

    return InlineKeyboardMarkup(keyboard)


# <<< Inline Keyboard <<<

# >>> User timezone setup >>>
async def start(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    main_menu_keyboard = make_main_menu_keyboard()

    if not helpers.is_a_user(user_id):
        await context.bot.send_message(chat_id=user_id,
                                       text="Welcome to TaskPrompt! Please enter your IANA timezone (e.g. \"Asia/Tehran\" or \"Europe/Berlin\").")
        # Await users' timezone entry
        return GET_TIMEZONE_STATE
    else:
        await context.bot.send_message(chat_id=user_id, text="What can I do for you today?", reply_markup=main_menu_keyboard)
        # Don't start the conversation of getting the timezone
        return ConvoH.END


async def get_timezone(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_input = update.message.text

    if not helpers.is_timezone_valid(user_input):
        await context.bot.send_message(chat_id=user_id,
                                       text="Doens't look like a valid IANA timezone. You could search for country's IANA and retry.")
        return GET_TIMEZONE_STATE

    helpers.create_user_profile(user_id, user_input)
    logger.info(f"User {user_id} registered with timezone {user_input}")

    main_menu_keyboard = make_main_menu_keyboard()

    await context.bot.send_message(chat_id=user_id,
                                   text=f"Your timezone has been set to {user_input}. What can I do for you today?",
                                   reply_markup=main_menu_keyboard)

    return ConvoH.END


async def cancel(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    logging.info(f"User {user_id} cancelled the timezone setup.")

    await context.bot.send_message(chat_id=user_id,
                                   text="You have cancelled timezone setup. You can always restart by tapping /start.")

    return ConvoH.END
# <<< User timezone setup <<<

# >>> Main Menu >>>
async def main_menu(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id

    main_menu_keyboard = make_main_menu_keyboard()

    await context.bot.send_message(chat_id=user_id, text="Here's the main menu:", reply_markup=main_menu_keyboard)
# <<< Main Menu <<<

# >>> Task Menu >>>
async def task_menu(update: Update, context: CT.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_tasks = helpers.format_tasks(helpers.get_user_tasks(user_id))
    await context.bot.send_message(chat_id=user_id, text=f"Yourr tasks: \n{user_tasks}")
# <<< Task Menu <<<


if __name__ == "__main__":
    # Load bot token from ./.env
    load_dotenv()
    TOKEN = getenv("BOT_TOKEN")
    # Initiate the DB
    helpers.db_initiator()

    persistence_file = "bot_data.pickle"
    persistence = PP(filepath=persistence_file)

    application = AB().token(TOKEN).persistence(persistence).build()

    setup_convo_handler = ConvoH(
        entry_points=[CH('start', start)],
        states={
            GET_TIMEZONE_STATE: [MH(filters.TEXT & ~filters.COMMAND, get_timezone)],
        },
        fallbacks=[CH('cancel', cancel)],
        allow_reentry=True
    )

    main_menu_handler = CH('menu', main_menu)

    application.add_handler(setup_convo_handler)
    application.add_handler(main_menu_handler)

    application.run_polling()
