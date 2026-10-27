
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.database import initialize_database, get_connection
from app.routes import results, admin, self_healing


limiter = Limiter(key_func=get_remote_address)


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

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


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
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()

        app.state.database_status = "connected"

        return {
            "status": "healthy",
            "database": "SQLite",
            "database_status": "connected"
        }

    except Exception:
        app.state.database_status = "disconnected"

        return {
            "status": "degraded",
            "database": "SQLite",
            "database_status": "disconnected"
        }
