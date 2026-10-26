from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

from app.routes.admin import verify_admin
from app.database import fetch_incidents, insert_incident

router = APIRouter()


@router.get("/incidents")
def get_incidents(
    authorization: str = Header(default="")
):
    verify_admin(authorization)

    try:
        return {"incidents": fetch_incidents()}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve incidents"
        )


@router.post("/incidents/test")
def create_test_incident(
    authorization: str = Header(default="")
):
    verify_admin(authorization)

    try:
        incident = insert_incident(
            incident_type="manual_test",
            message="Test incident created by admin",
            timestamp=datetime.now(timezone.utc).isoformat(),
            status="recorded"
        )

        return {
            "recorded": True,
            "incident": incident
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to record incident"
        )