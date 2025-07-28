# /handlers/tasks/task_menu_handler.py

# GENERAL PYTHON imports ->
import logging
# TELEGRAM BOT imports ->
from telegram import Update
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler,
)
# LOCAL imports ->
from config import VIEW_MENU, VIEW_TASKS_STATE
from handlers.common.common_handlers import (
    close_all_convos, 
    return_to_menu,
    delete_previous_menu,
    send_new_menu,
    edit_previous_menu
)
from handlers.common.inline_keyboards_module import tasks_keyboard
from helpers.user_data_util_classes.user_class import User

logger = logging.getLogger(__name__)


# >>> Task Menu >>>
async def view_task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user info and tasks
    user_id = update.effective_chat.id

    user_at_hand = User(user_id)
    

    if not user_at_hand._is_a_user:
        text = "You have not registered your timezone! You can do so tapping the /start command."

        await delete_previous_menu(update, context)
        await send_new_menu(update, context, text, None)
        
        raise ApplicationHandlerStop(ConversationHandler.END)
    else:
        user_tasks_list = user_at_hand.task.get_user_tasks()
        if user_tasks_list:
            user_tasks = "\n".join(user_tasks_list)
        else:
            user_tasks = "\n".join("--NO TASKS ADDED YET--")


        # Setting up keyboard markup
        tasks_markup = tasks_keyboard()

        # Unsuccessful task retrieval text
        add_task_guide_text = "No tasks are added yet. Try adding one by touching the button \"➕ Add\" or through the command /add_task task:priority(1, 2 or 3). \nExample: /add_task Go shopping:2\n" + ("\n".join("---NO TASKS ADDED YET---"))
        task_retrieval = f"Tasks:\n{user_tasks}"

        query = update.callback_query
        await query.answer()
        context.user_data['main_menu_message_id'] = query.message.message_id

        if user_tasks_list and user_tasks:
            await edit_previous_menu(update, context, task_retrieval, tasks_markup)
        else:
            await edit_previous_menu(update, context, add_task_guide_text, tasks_markup)

        del user_at_hand
        return VIEW_TASKS_STATE


def get_task_menu_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points = [
            CallbackQueryHandler(pattern='^menu_view_tasks$', callback=view_task_menu),
        ],
        states = {
            VIEW_TASKS_STATE : [
                CallbackQueryHandler(pattern='^tasks_return$', callback=return_to_menu),
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
