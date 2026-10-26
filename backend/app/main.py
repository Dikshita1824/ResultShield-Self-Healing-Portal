from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.database import initialize_database
from app.routes import results, admin, self_healing


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    app.state.database_status = "connected"

    print("ResultShield SQLite database initialized successfully!")

    yield


app = FastAPI(
    title="ResultShield API",
    description="Self-Healing University Result Portal",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(
    results.router,
    prefix="/api/results",
    tags=["Student Results"]
)

app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)

app.include_router(
    self_healing.router,
    prefix="/api/self-healing",
    tags=["Self-Healing"]
)


@app.get("/")
def home():
    return {
        "project": "ResultShield",
        "message": "Python backend is running",
        "database": "SQLite"
    }


@app.get("/api/health")
def health():
    database_status = getattr(
        app.state,
        "database_status",
        "not checked"
    )

    return {
        "status": (
            "healthy"
            if database_status == "connected"
            else "degraded"
        ),
        "database": "SQLite",
        "database_status": database_status
    }