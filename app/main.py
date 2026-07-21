from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.rate_limiter import limiter
from app.routers import auth, users, tasks

# Creates tables on startup if they don't exist yet. For a production system
# with evolving schemas, this would be replaced by Alembic migrations
# (a starter alembic/ setup is included in this repo).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description=(
        "A production-style Task Management REST API demonstrating JWT auth, "
        "pagination, filtering, rate limiting, and auto-generated OpenAPI docs."
    ),
    version="1.0.0",
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)


@app.get("/health", tags=["health"])
def health_check():
    """Simple liveness/readiness probe for load balancers and container orchestrators."""
    return {"status": "ok"}
