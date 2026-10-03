import sqlite3
from typing import List, Tuple

DB_PATH = "assistant_memory.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS profile (
                key TEXT PRIMARY KEY,
                value TEXT
            )"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS journal_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        # Prepopulate default persona profile values
        cursor.execute("INSERT OR IGNORE INTO profile VALUES ('user_name', 'Pratik')")
        cursor.execute("INSERT OR IGNORE INTO profile VALUES ('preferences', 'Prefers concise, actionable answers')")
        conn.commit()

def get_recent_context(limit: int = 5) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM profile")
        profile = ", ".join([f"{k}: {v}" for k, v in cursor.fetchall()])

        cursor.execute(
            "SELECT category, content, timestamp FROM journal_memory ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        logs = cursor.fetchall()
        logs_str = "; ".join([f"[{row[0]}] {row[1]}" for row in logs])

    return f"User Profile: {profile}. Recent Context/Logs: {logs_str}."

def log_event(category: str, content: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO journal_memory (category, content) VALUES (?, ?)",
            (category, content)
        )
        conn.commit()
