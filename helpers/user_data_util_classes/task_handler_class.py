# /helpers/user_data_util_classes/task_handler_class.py

# GENERAL PYTHON imports ->
from datetime import datetime
from sqlite3 import Error
# LOCAL imports ->
from helpers.db_utils import execute_query
from config import FORMAT_STRING_DATE, FORMAT_STRING_C

class TaskHandler:
    def __init__(self, uid: int):
        self.uid = uid

    def __str__(self):
        print("__STR__: This class serves to add, get, and remove tasks to and from the database.")

    def get_user_tasks(self) -> list | None:
        
        date = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        query = (
            "SELECT * FROM tasks "
            "WHERE (user_id = ? AND (created_at LIKE ?)) "
            "ORDER BY priority ASC,created_at ASC "
        )
        try:
            today_tasks = execute_query(query, (self._uid, date), True)
        except Error:
            return None
        else:
            if today_tasks:
                formatted_list = []
                for (index, task) in enumerate(today_tasks):
                    priority = "🔥" * task[3]
                    is_done = "✅" if task[4] == 1 else "🔲"
                    formatted_string = f"|{"0" if index <= 8 else ""}{index+1}|-- {task[2]} -- {priority} -- ({is_done})"
                    formatted_list.append(formatted_string)

                return formatted_list
            else:
                return None
           
    def add_user_task(self, task: str, priority: int) -> int:

        user_current_time_string = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_C)

        if priority in [1, 2, 3]:
            try:
                execute_query("INSERT INTO tasks (user_id, content, priority, created_at) VALUES (?, ?, ?, ?)",
                            (self._uid, task, priority, user_current_time_string))
            except Error:
                return 2
        else:
            return 1

        return 0
    
    def remove_user_task(self, task: str) -> int:
        try:
            execute_query("DELETE FROM tasks WHERE (user_id = ? AND content = ?)", (self._uid, task))
        except Error:
            return 1
        
        return 0
    
    def mark_done_and_return_new_list(self, task: str) -> list | int | None:
        user_local_date = datetime.strftime(self.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        update_query = "UPDATE tasks SET is_done = TRUE WHERE (user_id = ? AND content = ? AND (created_at LIKE ?))"
        try:
            execute_query(update_query, (self._uid, task, user_local_date))
        except Error:
            return 1
        else:
            refetched_user_tasks = self.get_user_tasks()
            return refetched_user_tasks