import sqlite3
import json
from datetime import datetime

DB_NAME = "pathfinder.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users: username, password
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     username
                     TEXT
                     PRIMARY
                     KEY,
                     password
                     TEXT
                 )''')
    # Chats: username, thread_id, role, message, timestamp
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     username
                     TEXT,
                     thread_id
                     TEXT,
                     role
                     TEXT,
                     message
                     TEXT,
                     timestamp
                     DATETIME
                 )''')
    conn.commit()
    conn.close()


def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None


def save_chat_message(username, thread_id, role, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO chats (username, thread_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, thread_id, role, message, datetime.now()))
    conn.commit()
    conn.close()


def get_chat_history(username, thread_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Fetch previous messages for this specific thread
    c.execute("SELECT role, message FROM chats WHERE username=? AND thread_id=? ORDER BY timestamp ASC",
              (username, thread_id))
    rows = c.fetchall()
    conn.close()

    # Convert to format LangChain expects
    # (role, content) tuples or dictionaries
    messages = []
    for r in rows:
        role = "human" if r[0] == "user" else "ai"
        messages.append((role, r[1]))
    return messages