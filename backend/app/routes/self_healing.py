
from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Header, HTTPException

from app.routes.admin import verify_admin
from app.database import fetch_incidents, insert_incident

router = APIRouter()
active_failures = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def log_event(failure_type, message, status):
    return insert_incident(
        incident_type=failure_type,
        message=message,
        timestamp=now(),
        status=status
    )


FAILURES = {
    "backend": {
        "title": "Backend availability test",
        "diagnosis": "Watchdog monitoring is required to restart a stopped backend process.",
        "action": "Backend failure scenario recorded; external watchdog is not yet connected."
    },
    "database": {
        "title": "Database connection test",
        "diagnosis": "Database connectivity must be checked before serving result queries.",
        "action": "Recovery check will verify that SQLite is reachable."
    },
    "invalid-record": {
        "title": "Invalid student record test",
        "diagnosis": "A student record must have valid marks within its allowed range.",
        "action": "Invalid-record scenario recorded without modifying student data."
    },
    "traffic": {
        "title": "Traffic spike test",
        "diagnosis": "Excess requests can overload the portal.",
        "action": "Traffic scenario recorded; request rate limiting must be enabled separately."
    }
}


@router.get("/incidents")
def get_incidents(authorization: str = Header(default="")):
    verify_admin(authorization)

    try:
        incidents = fetch_incidents()

        
        latest_incidents = incidents[:10]

        return {
            "incidents": latest_incidents,
            "total_incidents": len(incidents),
            "displayed_incidents": len(latest_incidents)
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve incident history"
        ) from exc


@router.get("/status")
def get_status(authorization: str = Header(default="")):
    verify_admin(authorization)

    return {
        "status": "degraded" if active_failures else "healthy",
        "active_failures": list(active_failures.keys()),
        "active_count": len(active_failures),
        "note": "Backend crash recovery and traffic limiting require separate mechanisms."
    }


@router.post("/chaos/{action}")
def run_chaos_test(
    action: str,
    authorization: str = Header(default="")
):
    verify_admin(authorization)

    if action not in FAILURES:
        raise HTTPException(status_code=404, detail="Unknown failure scenario")

    details = FAILURES[action]
    started = monotonic()

    try:
        log_event(
            action,
            f"Detected: {details['title']}",
            "detected"
        )

        log_event(
            action,
            f"Diagnosed: {details['diagnosis']}",
            "diagnosed"
        )

        active_failures[action] = {
            **details,
            "started": started,
            "detected_at": now()
        }

        log_event(
            action,
            f"Action taken: {details['action']}",
            "action_taken"
        )

        return {
            "success": True,
            "failure": action,
            "status": "detected",
            "message": details["title"],
            "diagnosis": details["diagnosis"],
            "action_taken": details["action"],
            "recovered": False,
            "note": "Scenario recorded. Use Recover System to run the available recovery checks."
        }

    except Exception as exc:
        active_failures.pop(action, None)
        raise HTTPException(
            status_code=503,
            detail="Unable to record failure scenario"
        ) from exc


@router.post("/recover")
def recover_system(authorization: str = Header(default="")):
    verify_admin(authorization)

    recovered = []
    failed = []

    for failure_type, details in list(active_failures.items()):
        started = details["started"]

        try:
            if failure_type == "database":
                
                fetch_incidents()

            if failure_type == "backend":
                
                log_event(
                    failure_type,
                    "Backend process is responding; external watchdog restart is not implemented yet.",
                    "recovery_limited"
                )
                failed.append(failure_type)
                continue

            if failure_type == "traffic":
                log_event(
                    failure_type,
                    "Traffic test recorded, but rate limiting is not implemented yet.",
                    "recovery_limited"
                )
                failed.append(failure_type)
                continue

            elapsed_ms = round((monotonic() - started) * 1000, 2)

            log_event(
                failure_type,
                f"Recovered: {details['title']}. Recovery-check duration: {elapsed_ms} ms.",
                "recovered"
            )

            recovered.append({
                "failure": failure_type,
                "recovery_time_ms": elapsed_ms,
                "status": "recovered"
            })

            active_failures.pop(failure_type, None)

        except Exception:
            log_event(
                failure_type,
                f"Recovery check failed for {details['title']}.",
                "recovery_failed"
            )
            failed.append(failure_type)

    return {
        "success": len(failed) == 0,
        "status": "healthy" if not active_failures else "degraded",
        "recovered": recovered,
        "failed": failed,
        "active_failures": list(active_failures.keys()),
        "message": (
            "All available recovery checks passed."
            if not failed
            else "Some mechanisms are not implemented yet. See incident history."
        )
    }


@router.post("/incidents/test")
def create_test_incident(authorization: str = Header(default="")):
    verify_admin(authorization)

    try:
        incident = log_event(
            "manual_test",
            "Test incident created by administrator.",
            "recorded"
        )
        return {"recorded": True, "incident": incident}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to record test incident"
        ) from exc
