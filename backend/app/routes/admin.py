import os
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.database import fetch_students

router = APIRouter()
active_tokens = set()


class AdminLogin(BaseModel):
    username: str
    password: str


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
def list_students(
    authorization: str = Header(default="")
):
    verify_admin(authorization)

    try:
        return fetch_students()

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve student records"
        )