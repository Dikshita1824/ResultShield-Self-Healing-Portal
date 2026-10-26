
from fastapi import APIRouter, HTTPException
from app.database import fetch_student

router = APIRouter()


@router.get("/{roll_number}")
def get_result(roll_number: str):
    try:
        student = fetch_student(roll_number)

        if student is None:
            raise HTTPException(
                status_code=404,
                detail="Result not found for this roll number"
            )

        return {
            "status": "success",
            "student": student
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve result"
        )