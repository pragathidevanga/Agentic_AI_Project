import sqlite3

DB_NAME = "student_time.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT,
            subject TEXT,
            time_slot TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    conn.close()


def save_schedule(day, subject, time_slot):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO schedule (day, subject, time_slot) VALUES (?, ?, ?)",
        (day, subject, time_slot)
    )

    conn.commit()
    conn.close()


def get_pending_tasks():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT day, subject, time_slot FROM schedule WHERE status='pending'"
    )
    rows = cur.fetchall()

    conn.close()
    return rows
