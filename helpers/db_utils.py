# /helpers/db_utils.py

# GENERAL PYTON imports ->
import sqlite3
# LOCAL imports ->
from config import DATA_DIR, DATABASE_FILE


def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """A util function for reading and writing data from and to the databace

    This function acts as the central database utility function to ease connection
    to the database file. It takes the queries and parameters provided to it and 
    run them by the database (using Python's native sqlite3) in a controlled-flow 
    structure and commits the changes made to the database if user didn't require
    a result (if fetch is set to False, in other words.)

    Args:
        query (str): An SQL query of any sorts.
        params (tuple, optional): The parameters that will replace \
        the question marks in the query. Defaults to ().
        fetch (bool, optional): Determines if the user requires anything \
        in return for the query they passed (SELECT queries). If set to \
        false :executre_query will commit changes (if there would be any). \
        Defaults to False.

    Returns:
        list | None: If the query has a return value (logically or syntactically),
        it will return a list of the rows (each row as a tuple) that SQL gave back.\
        Otherwise, return value would be None.
        
    """
    
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            fetched = cursor.fetchall()
            if len(fetched) > 0:
                return fetched
            else:
                return None
        else:
            conn.commit()
            return None

def db_initiator():
    DATA_DIR.mkdir(parents=True, exist_ok=True) # Checking for database directory existence

    with sqlite3.connect(DATABASE_FILE) as conn: # Try to recreate database schema if doesn't exist
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users(
                telegram_id INTEGER UNIQUE PRIMARY KEY,
                utc_offset TEXT,
                IANA_timezone TEXT,
                reminder_done_enabled BOOLEAN DEFAULT 0,
                reminder_left_enabled BOOLEAN DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
                user_id INTEGER, 
                content TEXT,
                priority INTEGER CHECK (priority IN (1, 2, 3)), 
                is_done BOOLEAN DEFAULT 0, 
                created_at TIMESTAMP, 
                FOREIGN KEY (user_id) REFERENCES users(telegram_id));
            CREATE TABLE IF NOT EXISTS reminders(
                user_id INTEGER,
                type TEXT CHECK (type IN ('DONE', 'LEFT')),
                reminder_time_locale TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );
            CREATE INDEX IF NOT EXISTS idx_telegram_id ON users(telegram_id);
        ''')