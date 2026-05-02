"""
backend/app/main.py

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"AgentEval API starting — version {settings.VERSION}")
    await create_tables()
    print("Database tables ready")
    yield
    print("AgentEval API shutting down")


app = FastAPI(
    title="AgentEval",
    description="The missing test framework for AI agents.",
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION}