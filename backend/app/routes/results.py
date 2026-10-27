
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import fetch_student_with_repair

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/{roll_number}")
@limiter.limit("10/minute")
def get_result(request: Request, roll_number: str):
    try:
        student = fetch_student_with_repair(roll_number)

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Result not found or could not be recovered"
            )

        return {
            "status": "success",
            "student": student
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve or recover result"
        ) from exc

