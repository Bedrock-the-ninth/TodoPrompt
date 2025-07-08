import sqlite3

def execute_query(query, params=(), fetch=False):
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor
        cursor.execute(query, params)
        return cursor.fetchall() if fetch else None
    
