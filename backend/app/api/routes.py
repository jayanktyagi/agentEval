"""
backend/app/api/routes.py

All HTTP endpoints for AgentEval.

POST /runs          — submit an AgentTest, kick off a test run
GET  /runs          — list all runs
GET  /runs/{run_id} — get a single run with full results
"""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.store import store
from app.models import AgentTest, TestRun, TestStatus
from app.runner.engine import run_test

router = APIRouter()


@router.post("/runs", response_model=TestRun, status_code=202)
async def create_run(test: AgentTest, background_tasks: BackgroundTasks):
    """
    Submit an AgentTest configuration and start a test run.

    Returns immediately with a TestRun in RUNNING status.
    Poll GET /runs/{run_id} to check progress.

    Example request body:
    {
        "name": "Flight Booking Agent",
        "agent_endpoint": "http://localhost:8080/run",
        "task_description": "Book a flight from Karachi to Dubai",
        "expected_tools": ["search_flights", "check_availability", "book_ticket"],
        "max_steps": 10
    }
    """
    run = TestRun(test=test, status=TestStatus.RUNNING)
    store.save(run)

    # Run the test in the background so we can return 202 immediately
    background_tasks.add_task(run_test, run)

    return run


@router.get("/runs", response_model=list[TestRun])
async def list_runs():
    """Return all test runs, most recent first."""
    runs = store.all()
    return sorted(runs, key=lambda r: r.started_at, reverse=True)


@router.get("/runs/{run_id}", response_model=TestRun)
async def get_run(run_id: UUID):
    """Get a single test run by ID. Poll this to check if your run is complete."""
    run = store.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return run