import sqlite3


def get_connection():
    conn = sqlite3.connect("tickets.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tickets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT, email TEXT, subject TEXT,
                  description TEXT, status TEXT,
                  created_at TEXT, updated_at TEXT,
                  comments TEXT)""")
    conn.commit()
    return conn, c
