# # handlers/task_menu_handler.py
# from telegram import Update
# from telegram.ext import (
#     CallbackQueryHandler, 
#     CommandHandler, 
#     ContextTypes,
#     ConversationHandler, 
#     filters, 
#     MessageHandler   
# )
# import asyncio

# # State Definition for ConversationHandlers
# VIEW_TASKS_STATE = 2
# ADD_TASK_STATE = 3
# REMOVE_TASK_STATE = 4


# # >>> Task Menu >>>
# async def task_menu(update: Update, context: CT.DEFAULT_TYPE):
#     user_id = update.effective_chat.id
#     user_tasks = helpers.format_tasks(helpers.get_user_tasks(user_id))
#     await context.bot.send_message(chat_id=user_id, text=f"Yourr tasks: \n{user_tasks}")



# task_convo_handler = ConvoH(
#         entry_points = [
#             CQH(pattern='^menu_view_tasks$', callback=task_menu),
#             CH('tasks', task_menu)
#         ],
#         states = {
#             VIEW_TASKS_STATE : [
#                 CQH(pattern='^tasks_add', callback=add_tasks_view),
#                 CQH(pattern='^tasks_remove', callback=remove_tasks_view),
#                 CQH(pattern='^tasks_return_btn', callback=return_to_main_menu)
#             ],
#             ADD_TASK_STATE : [
#                 MH(filters.TEXT & ~filters.COMMAND, recieve_new_task),
#                 CQH(pattern='^subtasks_return', callback=retrurn_to_tasks)
#             ],
#             REMOVE_TASK_STATE: [
#                 MH(filters.TEXT & ~filters.COMMAND, remove_task),
#                 CQH
#             ]
#         },
#         fallbacks = [
#             CQH(pattern="^return_button$", callback=task_menu),
#             CH('cancel', cancel)
#         ],
#         map_to_parent = {
#             ConvoH.END : ConvoH.END
#         },
#         allow_reentry = True
#     )


# def get_task_menu_handler() -> ConversationHandler:
