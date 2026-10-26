import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).resolve().parent.parent / "resultshield.db"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                roll_number TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                course TEXT NOT NULL DEFAULT 'BCA',
                semester INTEGER NOT NULL DEFAULT 5,
                marks INTEGER NOT NULL DEFAULT 0,
                max_marks INTEGER NOT NULL DEFAULT 100,
                result TEXT NOT NULL DEFAULT 'Pass'
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        existing = connection.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        if existing == 0:
            students = [
                ("101", "Aarav Sharma", "BCA", 5, 85, 100, "Pass"),
                ("102", "Priya Verma", "BCA", 5, 92, 100, "Pass"),
                ("103", "Rohan Singh", "BCA", 5, 76, 100, "Pass")
            ]

            connection.executemany("""
                INSERT INTO students
                (roll_number, name, course, semester, marks, max_marks, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, students)


def fetch_student(roll_number):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM students WHERE roll_number = ?",
            (roll_number,)
        ).fetchone()

        return dict(row) if row else None


def fetch_students():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM students ORDER BY roll_number"
        ).fetchall()

        return [dict(row) for row in rows]


def fetch_incidents():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, type, message, timestamp, status
            FROM incidents
            ORDER BY id DESC
            LIMIT 100
        """).fetchall()

        return [dict(row) for row in rows]


def insert_incident(incident_type, message, timestamp, status):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO incidents (type, message, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (incident_type, message, timestamp, status))

        return {
            "id": cursor.lastrowid,
            "type": incident_type,
            "message": message,
            "timestamp": timestamp,
            "status": status
        }