# /helpers/user_data_util_classes/task_handler_class.py

# GENERAL PYTHON imports ->
from datetime import datetime
from sqlite3 import Error
# LOCAL imports ->
from helpers.db_utils import execute_query
from helpers.user_data_util_classes.time_module import TimeManager
from config import FORMAT_STRING_DATE, FORMAT_STRING_C

class TaskManager:
    """This class, contains methods for getting, adding, deleting, and \
        marking tasks done on(to) to the database. 
    """
    def __init__(self, uid: int):
        self._uid = uid
        self.time = TimeManager(self._uid)

    def __str__(self):
        print("__STR__: This class serves to add, get, and remove tasks to and from the database.")

    def get_user_tasks(self) -> list[str] | None:
        """Getting user's tasks from the database

        Returns:
            list[str] | None: Either returns a list of formatted strings \
            or None if user entered no new tasks or simply something \
            goes wrong with executing the query.
        """
        date = datetime.strftime(self.time.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        query = (
            "SELECT * FROM tasks "
            "WHERE (user_id = ? AND (created_at LIKE ?)) "
            "ORDER BY priority DESC, created_at ASC "
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
        """Adds user tasks based on the priority and task string they have sent

        Args:
            task (str): a string that user inputs as their task
            priority (int): an integer from 1 to 3 indicating the \
            the priority or the urgency of the task

        Returns:
            int: A 2 return value would mean that something went wrong \
            executing the query. 1 Would mean the number entered is out \
            range (not a 1, 2, or a 3). 0 Would mean success.
        """
        user_current_time_string = datetime.strftime(self.time.get_user_local_time(), FORMAT_STRING_C)

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
        """This method searches for the task and removes it from \
        the database.

        Args:
            task (str): The entered tasks desired to be removed

        Returns:
            int: The return value of 1 would mean an error in the \
            processing of the query, whereas a 0 would mean success in \
            removing the task
        """
        try:
            execute_query("DELETE FROM tasks WHERE (user_id = ? AND content = ?)", (self._uid, task))
        except Error:
            return 1
        
        return 0
    
    def mark_done_and_return_new_list(self, task: str) -> list | int | None:
        """Marks the desired tasks done and returns the updated list of \
        formatted tasks.

        Args:
            task (str): The desired tasks to be marked done passed in \
            as a string.

        Returns:
            list | int | None: If operation successful, return value would \
            be a list of formatted (tasks + the task that was newly marked done). \
            If there were no tasks in the day's list, it would return a None \
            Otherwise, query execution error would be indicated by a value of 1.
        """
        user_local_date = datetime.strftime(self.time.get_user_local_time(), FORMAT_STRING_DATE) + "%"
        update_query = "UPDATE tasks SET is_done = TRUE WHERE (user_id = ? AND content = ? AND (created_at LIKE ?))"
        try:
            execute_query(update_query, (self._uid, task, user_local_date))
        except Error:
            return 1
        else:
            refetched_user_tasks = self.get_user_tasks()
            return refetched_user_tasks