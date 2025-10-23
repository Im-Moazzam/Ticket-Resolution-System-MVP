import sqlite3
import hashlib

conn = sqlite3.connect("tickets.db")
c = conn.cursor()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Example admin user
username = "admin"
email = "admin@example.com"
password = "1234"

c.execute(
    "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'admin')",
    (username, email, hash_password(password)),
)
conn.commit()
conn.close()
