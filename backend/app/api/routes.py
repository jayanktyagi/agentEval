"""
backend/app/api/routes.py

All HTTP endpoints for AgentEval.

POST /runs          — submit an AgentTest, enqueue the run, return 202
GET  /runs          — list all runs from Postgres
GET  /runs/{run_id} — get a single run (memory first, then Postgres)
GET  /health        — queue and database health check
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.store import store
from app.db.database import get_session
from app.db.repository import get_run, list_runs, save_run
from app.models import AgentTest, TestRun, TestStatus
from app.core.queue import enqueue_run, get_redis

router = APIRouter()


@router.post("/runs", response_model=TestRun, status_code=202)
async def create_run(
    test: AgentTest,
    session: AsyncSession = Depends(get_session),
):
    """
    Submit an AgentTest and enqueue it for execution.

    Returns immediately with status=running.
    Poll GET /runs/{run_id} to check progress.
    """
    run = TestRun(test=test, status=TestStatus.RUNNING)

    # Save to memory so the worker can find it
    store.save(run)

    # Save to Postgres immediately so it shows up in list even before completion
    await save_run(session, run)

    # Push onto Redis queue — worker picks this up
    enqueue_run(str(run.run_id))

    return run


@router.get("/runs", response_model=list[TestRun])
async def list_all_runs(session: AsyncSession = Depends(get_session)):
    """Return all test runs from Postgres, most recent first."""
    return await list_runs(session)


@router.get("/runs/{run_id}", response_model=TestRun)
async def get_single_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single test run by ID — always reads from Postgres.
    """
    run = await get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return run


@router.get("/queue/health")
async def queue_health():
    """Check Redis queue health — useful for monitoring."""
    try:
        redis = get_redis()
        redis.ping()
        from rq import Queue
        q = Queue("agenteval", connection=redis)
        return {
            "status": "ok",
            "queued_jobs": len(q),
            "redis": "connected",
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "redis": "disconnected",
        }