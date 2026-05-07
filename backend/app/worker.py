"""
backend/app/worker.py

The RQ worker entry point.

Fetches the TestRun from Postgres (not in-memory store)
because the worker runs in a separate process and cannot
access the API server's memory.
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


def execute_run(run_id: str) -> dict:
    """
    Execute a test run. Called by the RQ worker for each job.

    Fetches the run from Postgres, runs all scenarios,
    saves results back to Postgres.
    """
    from uuid import UUID
    from app.runner.engine import run_test
    from app.models import TestRun, TestStatus

    logger.info("Worker picked up run %s", run_id)

    async def _execute():
        from app.db.database import SessionLocal, create_tables
        from app.db.repository import get_run, save_run

        await create_tables()

        async with SessionLocal() as session:
            run = await get_run(session, UUID(run_id))

        if not run:
            logger.error("Run %s not found in Postgres", run_id)
            return {"error": f"Run {run_id} not found"}

        # Also put it in the in-memory store so routes can read it
        from app.core.store import store
        store.save(run)

        try:
            await run_test(run)
            logger.info(
                "Worker completed run %s — %d/%d passed",
                run_id, run.passed, run.total_scenarios,
            )
            return {
                "run_id": run_id,
                "status": run.status,
                "passed": run.passed,
                "total": run.total_scenarios,
                "pass_rate": run.pass_rate,
            }
        except Exception as exc:
            logger.error("Worker failed on run %s: %s", run_id, exc)
            run.status = TestStatus.ERROR
            async with SessionLocal() as session:
                from app.db.repository import save_run
                await save_run(session, run)
            return {"run_id": run_id, "error": str(exc)}

    return asyncio.run(_execute())


if __name__ == "__main__":
    from redis import Redis
    from rq import SimpleWorker
    from app.core.config import settings

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    redis_conn = Redis.from_url(settings.REDIS_URL)
    worker = SimpleWorker(["agenteval"], connection=redis_conn)

    print("AgentEval worker starting — listening on queue 'agenteval'")
    print(f"Redis: {settings.REDIS_URL}")
    worker.work(with_scheduler=False)