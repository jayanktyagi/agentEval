"""
backend/app/db/repository.py

All database read/write operations live here.

The rest of the app (routes, engine) never touches SQLAlchemy directly.
They call these functions and get back Pydantic models.

This is the only file that changes if we ever switch databases.
"""

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.orm import ScenarioResultORM, TestRunORM
from app.models import ScenarioResult, TestRun, TestStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _run_to_dict(run: TestRun) -> dict:
    """Convert a TestRun pydantic model to a JSON-serializable dict."""
    return json.loads(run.model_dump_json())


def _result_to_dict(result: ScenarioResult) -> dict:
    """Convert a ScenarioResult pydantic model to a JSON-serializable dict."""
    return json.loads(result.model_dump_json())


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

async def save_run(session: AsyncSession, run: TestRun) -> None:
    """
    Insert or update a TestRun in the database.

    Called after every scenario completes so partial results are always
    readable — not just at the end.
    """
    existing = await session.get(TestRunORM, run.run_id)

    if existing is None:
        # First save — insert
        orm_run = TestRunORM(
            id=run.run_id,
            name=run.test.name,
            agent_endpoint=run.test.agent_endpoint,
            task_description=run.test.task_description,
            status=run.status,
            total_scenarios=run.total_scenarios,
            passed=run.passed,
            failed=run.failed,
            pass_rate=run.pass_rate,
            test_config=_run_to_dict(run),
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        session.add(orm_run)
    else:
        # Subsequent saves — update metrics and status
        existing.status = run.status
        existing.total_scenarios = run.total_scenarios
        existing.passed = run.passed
        existing.failed = run.failed
        existing.pass_rate = run.pass_rate
        existing.test_config = _run_to_dict(run)
        existing.finished_at = run.finished_at

    await session.commit()
    logger.debug("Saved run %s to database", run.run_id)


async def save_result(session: AsyncSession, run_id: uuid.UUID, result: ScenarioResult) -> None:
    """Insert a single ScenarioResult row."""
    orm_result = ScenarioResultORM(
        run_id=run_id,
        scenario_type=result.scenario.scenario_type,
        title=result.scenario.title,
        status=result.status,
        failure_reason=result.failure_reason,
        failure_detail=result.failure_detail,
        failure_at_step=result.failure_at_step,
        tool_accuracy=result.tool_accuracy,
        step_efficiency=result.step_efficiency,
        total_steps=result.trace.total_steps,
        scenario_data=_result_to_dict(result),
        trace_data=json.loads(result.trace.model_dump_json()),
    )
    session.add(orm_result)
    await session.commit()
    logger.debug("Saved result for scenario '%s'", result.scenario.title)


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

async def get_run(session: AsyncSession, run_id: uuid.UUID) -> TestRun | None:
    """Fetch a single TestRun by ID. Returns None if not found."""
    stmt = (
        select(TestRunORM)
        .where(TestRunORM.id == run_id)
        .options(selectinload(TestRunORM.results))
    )
    result = await session.execute(stmt)
    orm_run = result.scalar_one_or_none()

    if orm_run is None:
        return None

    return TestRun.model_validate(orm_run.test_config)


async def list_runs(session: AsyncSession, limit: int = 50) -> list[TestRun]:
    """Return the most recent test runs, up to limit."""
    stmt = (
        select(TestRunORM)
        .order_by(TestRunORM.started_at.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    orm_runs = result.scalars().all()

    runs = []
    for orm_run in orm_runs:
        try:
            runs.append(TestRun.model_validate(orm_run.test_config))
        except Exception as exc:
            logger.warning("Failed to deserialize run %s: %s", orm_run.id, exc)
            continue

    return runs