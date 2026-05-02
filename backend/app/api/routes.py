"""
backend/app/api/routes.py

All HTTP endpoints for AgentEval.

POST /runs          — submit an AgentTest, kick off a test run
GET  /runs          — list all runs
GET  /runs/{run_id} — get a single run with full results
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.store import store
from app.db.database import get_session
from app.db.repository import get_run, list_runs
from app.models import AgentTest, TestRun, TestStatus
from app.runner.engine import run_test

router = APIRouter()


@router.post("/runs", response_model=TestRun, status_code=202)
async def create_run(
    test: AgentTest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Submit an AgentTest configuration and start a test run.

    Returns immediately with a TestRun in RUNNING status.
    Poll GET /runs/{run_id} to check progress.
    """
    run = TestRun(test=test, status=TestStatus.RUNNING)

    # Keep in memory for fast access during the run
    store.save(run)

    # Run the test in the background
    background_tasks.add_task(run_test, run)

    return run


@router.get("/runs", response_model=list[TestRun])
async def list_all_runs(session: AsyncSession = Depends(get_session)):
    """Return all test runs from the database, most recent first."""
    return await list_runs(session)


@router.get("/runs/{run_id}", response_model=TestRun)
async def get_single_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single test run by ID.

    Checks in-memory store first (for runs still in progress),
    then falls back to the database (for completed runs).
    """
    # Check memory first — run might still be in progress
    run = store.get(run_id)
    if run:
        return run

    # Fall back to database
    run = await get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return run