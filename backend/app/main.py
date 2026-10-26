
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# Allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Student Results Routes
app.include_router(
    results.router,
    prefix="/api/results",
    tags=["Student Results"]
)


# Admin Routes
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)


# Self-Healing Routes
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
