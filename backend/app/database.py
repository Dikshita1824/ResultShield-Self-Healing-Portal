
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).resolve().parent.parent / "resultshield.db"


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def is_valid_student(student):
    if not student:
        return False

    required_fields = (
        "roll_number", "name", "course",
        "semester", "marks", "max_marks", "result"
    )

    if any(student.get(field) is None for field in required_fields):
        return False

    try:
        marks = int(student["marks"])
        max_marks = int(student["max_marks"])
        semester = int(student["semester"])
    except (ValueError, TypeError, OverflowError):
        return False

    return (
        bool(str(student["roll_number"]).strip())
        and bool(str(student["name"]).strip())
        and bool(str(student["course"]).strip())
        and max_marks > 0
        and 0 <= marks <= max_marks
        and semester > 0
        and str(student["result"]).strip().lower() in ("pass", "fail")
    )


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

        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_backups (
                roll_number TEXT PRIMARY KEY,
                student_data TEXT NOT NULL,
                backed_up_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS quarantined_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT NOT NULL,
                student_data TEXT NOT NULL,
                reason TEXT NOT NULL,
                quarantined_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'quarantined'
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

    # Preserve the first valid backup for each student.
    # Do not overwrite an existing backup during startup.
    for student in fetch_students():
        save_student_backup(student, only_if_missing=True)


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


def save_student_backup(student, only_if_missing=False):
    if not is_valid_student(student):
        return False

    query = """
        INSERT INTO student_backups
            (roll_number, student_data, backed_up_at)
        VALUES (?, ?, ?)
        ON CONFLICT(roll_number) DO UPDATE SET
            student_data = excluded.student_data,
            backed_up_at = excluded.backed_up_at
    """

    if only_if_missing:
        query = """
            INSERT OR IGNORE INTO student_backups
                (roll_number, student_data, backed_up_at)
            VALUES (?, ?, ?)
        """

    with get_connection() as connection:
        connection.execute(query, (
            str(student["roll_number"]),
            json.dumps(student),
            current_timestamp()
        ))

    return True


def quarantine_student(student, reason):
    if not student or not student.get("roll_number"):
        raise ValueError("A student roll number is required for quarantine.")

    roll_number = str(student["roll_number"])
    timestamp = current_timestamp()

    with get_connection() as connection:
        # Keep the record and incident changes in one transaction.
        connection.execute("""
            INSERT INTO quarantined_students
                (roll_number, student_data, reason, quarantined_at, status)
            VALUES (?, ?, ?, ?, 'quarantined')
        """, (
            roll_number,
            json.dumps(student),
            reason,
            timestamp
        ))

        connection.execute("""
            INSERT INTO incidents (type, message, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (
            "invalid_record",
            f"Detected: roll {roll_number}; reason: {reason}",
            timestamp,
            "detected"
        ))

        connection.execute("""
            INSERT INTO incidents (type, message, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (
            "invalid_record",
            f"Diagnosed invalid student record: {roll_number}",
            current_timestamp(),
            "diagnosed"
        ))

        connection.execute("""
            INSERT INTO incidents (type, message, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (
            "invalid_record",
            f"Action taken: quarantined roll {roll_number}",
            current_timestamp(),
            "quarantined"
        ))

        connection.execute("""
            DELETE FROM students WHERE roll_number = ?
        """, (roll_number,))

    return True


def repair_student_from_backup(roll_number):
    roll_number = str(roll_number)

    with get_connection() as connection:
        backup = connection.execute("""
            SELECT student_data
            FROM student_backups
            WHERE roll_number = ?
        """, (roll_number,)).fetchone()

    if backup is None:
        return False

    try:
        student = json.loads(backup["student_data"])
    except (ValueError, TypeError):
        return False

    if not is_valid_student(student):
        return False

    if str(student["roll_number"]) != roll_number:
        return False

    with get_connection() as connection:
        # Restore only if the record is absent or currently invalid.
        current = connection.execute("""
            SELECT * FROM students WHERE roll_number = ?
        """, (roll_number,)).fetchone()

        if current is not None and is_valid_student(dict(current)):
            return False

        connection.execute("""
            INSERT OR REPLACE INTO students
                (roll_number, name, course, semester, marks, max_marks, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            roll_number,
            student["name"],
            student["course"],
            int(student["semester"]),
            int(student["marks"]),
            int(student["max_marks"]),
            student["result"]
        ))

        connection.execute("""
            UPDATE quarantined_students
            SET status = 'recovered'
            WHERE roll_number = ? AND status = 'quarantined'
        """, (roll_number,))

        connection.execute("""
            INSERT INTO incidents (type, message, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (
            "invalid_record",
            f"Recovered and verified backup for roll {roll_number}",
            current_timestamp(),
            "recovered"
        ))

    restored = fetch_student(roll_number)
    return is_valid_student(restored)


def fetch_student_with_repair(roll_number):
    student = fetch_student(roll_number)

    if student is None:
        return None

    if is_valid_student(student):
        return student

    reason = "Record failed student data validation."
    quarantine_student(student, reason)

    if repair_student_from_backup(roll_number):
        restored = fetch_student(roll_number)

        if is_valid_student(restored):
            return restored

    return None
