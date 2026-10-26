
import os
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.database import (
    fetch_student,
    fetch_students,
    get_connection,
    is_valid_student,
    save_student_backup,
)

router = APIRouter()
active_tokens = set()


class AdminLogin(BaseModel):
    username: str
    password: str


class StudentRecord(BaseModel):
    roll_number: str
    name: str
    course: str = "BCA"
    semester: int = 5
    marks: int
    max_marks: int = 100
    result: str


def validate_student_record(student):
    if not is_valid_student(student):
        raise HTTPException(
            status_code=422,
            detail="Invalid student record. Check marks, name, course and semester."
        )


@router.post("/login")
def admin_login(credentials: AdminLogin):
    expected_user = os.getenv("ADMIN_USERNAME", "admin")
    expected_password = os.getenv("ADMIN_PASSWORD", "admin123")

    valid_user = secrets.compare_digest(
        credentials.username,
        expected_user
    )
    valid_password = secrets.compare_digest(
        credentials.password,
        expected_password
    )

    if not (valid_user and valid_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token = secrets.token_urlsafe(32)
    active_tokens.add(token)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def verify_admin(authorization: Optional[str] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Admin login required"
        )

    token = authorization[7:]

    if token not in active_tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin session"
        )


@router.get("/students")
def list_students(authorization: str = Header(default="")):
    verify_admin(authorization)

    try:
        return fetch_students()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve student records"
        )


@router.post("/students", status_code=201)
def add_student(
    record: StudentRecord,
    authorization: str = Header(default="")
):
    verify_admin(authorization)
    student = record.model_dump()
    student["roll_number"] = student["roll_number"].strip()
    student["name"] = student["name"].strip()
    student["course"] = student["course"].strip()
    student["result"] = student["result"].strip().title()

    validate_student_record(student)

    if fetch_student(student["roll_number"]) is not None:
        raise HTTPException(
            status_code=409,
            detail="A student with this roll number already exists"
        )

    try:
        with get_connection() as connection:
            connection.execute("""
                INSERT INTO students
                    (roll_number, name, course, semester, marks, max_marks, result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                student["roll_number"],
                student["name"],
                student["course"],
                student["semester"],
                student["marks"],
                student["max_marks"],
                student["result"]
            ))

        save_student_backup(student)

        return {
            "success": True,
            "message": "Student added and backup saved",
            "student": student
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to add student record"
        )


@router.put("/students/{roll_number}")
def update_student(
    roll_number: str,
    record: StudentRecord,
    authorization: str = Header(default="")
):
    verify_admin(authorization)

    if roll_number != record.roll_number:
        raise HTTPException(
            status_code=400,
            detail="URL roll number and record roll number must match"
        )

    student = record.model_dump()
    student["roll_number"] = student["roll_number"].strip()
    student["name"] = student["name"].strip()
    student["course"] = student["course"].strip()
    student["result"] = student["result"].strip().title()

    validate_student_record(student)

    if fetch_student(roll_number) is None:
        raise HTTPException(
            status_code=404,
            detail="Student record not found"
        )

    try:
        with get_connection() as connection:
            connection.execute("""
                UPDATE students
                SET name = ?, course = ?, semester = ?,
                    marks = ?, max_marks = ?, result = ?
                WHERE roll_number = ?
            """, (
                student["name"],
                student["course"],
                student["semester"],
                student["marks"],
                student["max_marks"],
                student["result"],
                roll_number
            ))

        save_student_backup(student)

        return {
            "success": True,
            "message": "Student updated and backup refreshed",
            "student": student
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to update student record"
        )
