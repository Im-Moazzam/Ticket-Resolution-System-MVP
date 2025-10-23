import sqlite3


def get_connection():
    conn = sqlite3.connect("tickets.db", check_same_thread=False)
    c = conn.cursor()

    # --- Ticket Table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            subject TEXT,
            description TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            comments TEXT
        )
    """)

    # --- Users Table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)

    conn.commit()
    return conn, c
