"""FastAPI application entrypoint for ArchPilot."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes_health import router as health_router
from app.api.routes_runs import router as runs_router
from app.core.config import get_settings
from app.core.errors import ArchPilotException
from app.core.logging import logger
from app.db.session import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing %s v%s...", settings.PROJECT_NAME, settings.VERSION)
    init_db()
    yield
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


app = FastAPI(
    title="ArchPilot API",
    description=(
        "Evidence-Driven AI Engineering Decision Agent API.\n\n"
        "Transforms high-level technical tasks into structured engineering decisions via "
        "a bounded agentic loop: PLAN → ACT → OBSERVE → VALIDATE → RESPOND."
    ),
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Cross-Origin Resource Sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
@app.exception_handler(ArchPilotException)
async def archpilot_exception_handler(
    request: Request, exc: ArchPilotException
) -> JSONResponse:
    """Handle categorized domain errors with clean structure."""
    logger.warning("Domain exception on %s: %s", request.url.path, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.to_dict()},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request payload validation errors without exposing internal internals."""
    logger.warning("Validation failure on %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "TASK_INVALID",
                "message": "Input validation failure.",
                "details": exc.errors(),
            }
        },
    )



@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Fallback handler for uncaught server errors (shields internal traces from clients)."""
    logger.exception("Unhandled server exception on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "UNKNOWN_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {},
            }
        },
    )


# Register Routers
app.include_router(health_router)
app.include_router(runs_router)


@app.get("/", summary="Root index", tags=["System"])
async def root() -> dict[str, str]:
    """Service metadata and link to interactive documentation."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
    }
