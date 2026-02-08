import sqlite3
import json
from datetime import datetime

DB_NAME = "pathfinder.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # User Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (
                     username
                     TEXT
                     PRIMARY
                     KEY,
                     password
                     TEXT
                 )''')
    # Chat History Table
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
                     message
                     TEXT,
                     role
                     TEXT,
                     timestamp
                     DATETIME
                 )''')
    # Progress/Plan Table
    c.execute('''CREATE TABLE IF NOT EXISTS plans
                 (
                     username
                     TEXT,
                     topic
                     TEXT,
                     plan_json
                     TEXT,
                     progress
                     INTEGER
                     DEFAULT
                     0,
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


def save_chat(username, thread_id, role, message):
    if not username: return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO chats (username, thread_id, message, role, timestamp) VALUES (?, ?, ?, ?, ?)",
              (username, thread_id, message, role, datetime.now()))
    conn.commit()
    conn.close()


def get_user_history(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT thread_id, role, message FROM chats WHERE username=? ORDER BY timestamp ASC", (username,))
    rows = c.fetchall()
    conn.close()

    # Group by thread
    history = {}
    for r in rows:
        tid = r[0]
        if tid not in history: history[tid] = []
        history[tid].append({"role": r[1], "content": r[2]})
    return history