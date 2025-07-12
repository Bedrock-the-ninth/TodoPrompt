# handlers/task_menu_handler.py

# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
)
# DOMESTIC imports ->
from handlers.common_handlers import (
    close_all_convos, 
    return_to_menu,
    edit_previous_menu
)
from handlers.inline_keyboards_module import tasks_keyboard
from helpers.user_data_utils import User
# State Definition for ConversationHandlers
from config import VIEW_MENU, VIEW_TASKS_STATE



# >>> Task Menu >>>
async def view_task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user info and tasks
    user_id = update.effective_chat.id

    user_at_hand = User(user_id)
    user_tasks_list = user_at_hand.get_user_tasks()

    if user_tasks_list:
        user_tasks = "\n".join(user_tasks_list)
    else:
        user_tasks = None

    # Setting up keyboard markup
    tasks_markup = tasks_keyboard()

    # Unsuccessful task retrieval text
    unsuccessful_task_retrieval = "No tasks are added yet. Try adding one by touching the button \"➕ Add\"" \
    " or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2"
    task_retrieval = f"Tasks:\n{user_tasks}"

    query = update.callback_query
    await query.answer()
    context.user_data['main_menu_message_id'] = query.message.message_id

    if not user_tasks:
        await edit_previous_menu(update, context, unsuccessful_task_retrieval, tasks_markup)
    else:
        await edit_previous_menu(update, context, task_retrieval, tasks_markup)

    del user_at_hand
    return VIEW_TASKS_STATE



def get_task_menu_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^menu_view_tasks$', callback=view_task_menu),
        ],
        states = {
            VIEW_TASKS_STATE : [
                CallbackQueryHandler(pattern='^tasks_return$', callback=return_to_menu)
            ],
        },
        fallbacks = [
            CommandHandler('cancel', close_all_convos)
        ],
        map_to_parent = {
            ConversationHandler.END : VIEW_MENU
        },
        allow_reentry = True
    )
# <<< Task Menu <<<
