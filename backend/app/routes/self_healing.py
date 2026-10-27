from datetime import datetime, timezone
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.routes.admin import verify_admin
from app.database import (
    fetch_incidents,
    insert_incident,
    get_connection,
    fetch_student_with_repair,
    repair_student_from_backup,
)

router = APIRouter()
security = HTTPBearer()

# Active failures are stored while the backend process is running.
active_failures = {}

# Tracks simulated traffic pressure for the Chaos Lab.
simulated_traffic = False


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    authorization = f"{credentials.scheme} {credentials.credentials}"
    verify_admin(authorization)


def now():
    return datetime.now(timezone.utc).isoformat()


def log_event(failure_type, message, status):
    return insert_incident(
        incident_type=failure_type,
        message=message,
        timestamp=now(),
        status=status,
    )


def check_database():
    """Perform a real SQLite connectivity check."""
    with get_connection() as connection:
        connection.execute("SELECT 1").fetchone()

    return True


def find_invalid_students():
    """
    Find student records with missing names or invalid marks.
    Marks must be between 0 and 100.
    """
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT roll_number, name, marks
            FROM students
            WHERE name IS NULL
               OR TRIM(name) = ''
               OR marks IS NULL
               OR marks < 0
               OR marks > 100
            """
        ).fetchall()

    return [
        {
            "roll_number": str(row[0]),
            "name": row[1],
            "marks": row[2],
        }
        for row in rows
    ]


FAILURES = {
    "backend": {
        "title": "Backend availability test",
        "diagnosis": (
            "The Chaos Lab is simulating a backend availability incident. "
            "A separate watchdog is required to detect and restart a "
            "backend process that has completely stopped."
        ),
    },
    "database": {
        "title": "Database connectivity test",
        "diagnosis": (
            "The system will verify whether the SQLite database can "
            "execute a test query."
        ),
    },
    "invalid-record": {
        "title": "Invalid student record test",
        "diagnosis": (
            "The system will check student names and marks against "
            "the valid data rules."
        ),
    },
    "traffic": {
        "title": "Traffic spike test",
        "diagnosis": (
            "The Chaos Lab will simulate traffic pressure. The results "
            "endpoint has rate limiting configured."
        ),
    },
    "backup-unavailable": {
        "title": "Verified Backup Unavailable",
        "diagnosis": (
            "The requested recovery record has no verified backup. "
            "Automatic recovery cannot safely restore the original data. "
            "Manual data restoration is required."
        ),
    },
}


@router.get("/incidents")
def get_incidents(_=Depends(require_admin)):
    try:
        incidents = fetch_incidents()

        return {
            "incidents": incidents[:10],
            "total_incidents": len(incidents),
            "displayed_incidents": min(len(incidents), 10),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve incident history",
        ) from exc


@router.get("/status")
def get_status(_=Depends(require_admin)):
    return {
        "status": "degraded" if active_failures else "healthy",
        "active_failures": list(active_failures.keys()),
        "active_count": len(active_failures),
        "simulated_traffic": simulated_traffic,
        "note": (
            "Backend process restart requires an external watchdog. "
            "Database connectivity and invalid records can be checked "
            "using the available diagnostic routines. "
            "Recovery is not possible when a verified backup is missing."
        ),
    }


@router.post("/chaos/{action}")
def run_chaos_test(action: str, _=Depends(require_admin)):
    global simulated_traffic

    if action not in FAILURES:
        raise HTTPException(
            status_code=404,
            detail="Unknown failure scenario",
        )

    if action in active_failures:
        return {
            "success": True,
            "failure": action,
            "status": "already_active",
            "message": "This failure scenario is already active.",
            "active_failure": active_failures[action],
        }

    details = FAILURES[action]
    started = monotonic()
    detected = False
    diagnosis = details["diagnosis"]
    evidence = {}
    failure_status = "detection_failed"

    try:
        # Stage 1: Inject or initiate the selected scenario.
        log_event(
            action,
            f"Failure injection started: {details['title']}",
            "injection_started",
        )

        # Stage 2: Perform diagnostic checks.
        if action == "backend":
            # Simulation only: this does not stop the actual backend.
            detected = True
            evidence = {
                "mode": "simulated",
                "external_watchdog_available": False,
            }

        elif action == "database":
            try:
                check_database()

                detected = False
                failure_status = "healthy"
                evidence = {
                    "database": "SQLite",
                    "connectivity": "passed",
                    "injected_failure": False,
                }

            except Exception:
                detected = True
                evidence = {
                    "database": "SQLite",
                    "connectivity": "failed",
                }

        elif action == "invalid-record":
            invalid_records = find_invalid_students()
            detected = len(invalid_records) > 0

            evidence = {
                "invalid_record_count": len(invalid_records),
                "invalid_records": invalid_records[:10],
            }

            if not detected:
                failure_status = "healthy"

        elif action == "traffic":
            # Simulates pressure; it does not generate real traffic.
            simulated_traffic = True
            detected = True

            evidence = {
                "mode": "simulated",
                "rate_limit_configured": True,
            }

        elif action == "backup-unavailable":
            # Use a dummy roll number so real student data is untouched.
            demo_roll_number = "DEMO-NO-BACKUP-999"

            with get_connection() as connection:
                backup = connection.execute(
                    """
                    SELECT student_data
                    FROM student_backups
                    WHERE roll_number = ?
                    """,
                    (demo_roll_number,),
                ).fetchone()

            detected = backup is None

            evidence = {
                "roll_number": demo_roll_number,
                "verified_backup_available": backup is not None,
                "mode": "safe_simulation",
            }

            if not detected:
                failure_status = "healthy"

        # Stage 3: Record the diagnostic result.
        if detected:
            failure_status = "detected"

            active_failures[action] = {
                **details,
                "started": started,
                "detected_at": now(),
                "evidence": evidence,
            }

            log_event(
                action,
                f"Detection confirmed: {details['title']}. "
                f"Evidence: {evidence}",
                "detected",
            )

            log_event(
                action,
                f"Diagnosis: {diagnosis}",
                "diagnosed",
            )

        else:
            log_event(
                action,
                f"Diagnostic check passed: {details['title']}. "
                f"Evidence: {evidence}",
                "check_passed",
            )

        return {
            "success": True,
            "failure": action,
            "status": failure_status,
            "detected": detected,
            "message": (
                "Problem detected. Recovery can now be attempted."
                if detected
                else "No active problem was detected by this check."
            ),
            "diagnosis": diagnosis,
            "evidence": evidence,
            "recovered": False,
        }

    except Exception as exc:
        active_failures.pop(action, None)

        if action == "traffic":
            simulated_traffic = False

        try:
            log_event(
                action,
                "Diagnostic check could not be completed.",
                "detection_error",
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=503,
            detail="Diagnostic check could not be completed",
        ) from exc


@router.post("/recover")
def recover_system(_=Depends(require_admin)):
    global simulated_traffic

    recovered = []
    failed = []

    for failure_type, details in list(active_failures.items()):
        elapsed_ms = None

        try:
            started = details["started"]

            # The current process cannot restart itself through this route.
            if failure_type == "backend":
                log_event(
                    failure_type,
                    "Recovery not completed: an external watchdog "
                    "is required to restart a stopped backend process.",
                    "recovery_limited",
                )

                failed.append({
                    "failure": failure_type,
                    "status": "recovery_limited",
                    "message": "External watchdog is not implemented.",
                })
                continue

            # Verify database connectivity.
            if failure_type == "database":
                check_database()

            # Repair only records confirmed to be invalid.
            if failure_type == "invalid-record":
                invalid_records = find_invalid_students()
                repair_results = []

                for record in invalid_records:
                    roll_number = record["roll_number"]

                    try:
                        repaired_student = fetch_student_with_repair(
                            roll_number
                        )

                        remaining_invalid = find_invalid_students()
                        still_invalid = any(
                            item["roll_number"] == roll_number
                            for item in remaining_invalid
                        )

                        repair_results.append({
                            "roll_number": roll_number,
                            "verified": (
                                repaired_student is not None
                                and not still_invalid
                            ),
                        })

                    except Exception:
                        repair_results.append({
                            "roll_number": roll_number,
                            "verified": False,
                        })

                remaining_invalid = find_invalid_students()

                if remaining_invalid:
                    log_event(
                        failure_type,
                        "Recovery verification failed: invalid records "
                        "still exist.",
                        "recovery_failed",
                    )

                    failed.append({
                        "failure": failure_type,
                        "status": "recovery_failed",
                        "remaining_invalid_count": len(remaining_invalid),
                        "repair_results": repair_results,
                    })
                    continue

            # The demo record deliberately has no verified backup.
            if failure_type == "backup-unavailable":
                demo_roll_number = details["evidence"]["roll_number"]

                restored = repair_student_from_backup(
                    demo_roll_number
                )

                # No backup means safe restoration cannot be completed.
                if not restored:
                    log_event(
                        failure_type,
                        "Recovery failed: no verified backup exists "
                        "for the demo record. Manual data restoration "
                        "is required.",
                        "recovery_failed",
                    )

                    failed.append({
                        "failure": failure_type,
                        "status": "recovery_failed",
                        "reason": "No verified backup is available.",
                        "roll_number": demo_roll_number,
                    })
                    continue

            # End the simulated traffic incident and verify the state.
            if failure_type == "traffic":
                simulated_traffic = False

                if simulated_traffic:
                    raise RuntimeError(
                        "Simulated traffic pressure is still active."
                    )

            # Report success only after the applicable check passes.
            elapsed_ms = round(
                (monotonic() - started) * 1000,
                2,
            )

            log_event(
                failure_type,
                f"Recovery verification passed for "
                f"{details['title']}. Duration: {elapsed_ms} ms.",
                "recovered",
            )

            recovered.append({
                "failure": failure_type,
                "recovery_time_ms": elapsed_ms,
                "status": "recovered",
            })

            active_failures.pop(failure_type, None)

        except Exception:
            try:
                log_event(
                    failure_type,
                    f"Recovery verification failed for "
                    f"{details['title']}.",
                    "recovery_failed",
                )
            except Exception:
                pass

            failed.append({
                "failure": failure_type,
                "status": "recovery_failed",
                "message": "Recovery could not be verified.",
            })

    return {
        "success": len(failed) == 0,
        "status": "degraded" if active_failures else "healthy",
        "recovered": recovered,
        "failed": failed,
        "active_failures": list(active_failures.keys()),
        "message": (
            "All attempted recoveries passed verification."
            if not failed
            else "Some failures need additional recovery mechanisms."
        ),
    }


@router.post("/incidents/test")
def create_test_incident(_=Depends(require_admin)):
    try:
        incident = log_event(
            "manual_test",
            "Test incident created by administrator.",
            "recorded",
        )

        return {
            "recorded": True,
            "incident": incident,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to record test incident",
        ) from exc