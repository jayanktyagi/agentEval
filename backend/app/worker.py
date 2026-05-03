"""
backend/app/worker.py

The RQ worker entry point.

This file does two things:
1. Defines execute_run() — the function RQ calls for each job
2. Provides a __main__ block to start the worker process

Start the worker with:
    python -m app.worker

Or with the rq CLI:
    rq worker agenteval --url redis://localhost:6379

How it works:
- POST /runs enqueues a job with the run_id
- The worker picks up the job from Redis
- Calls execute_run(run_id)
- execute_run fetches the run from the in-memory store
- Runs all scenarios and saves results to Postgres
"""

import asyncio
import logging
import sys
import os

# Make sure backend/ is on the path when running as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.store import store
from app.models import TestStatus
from rq import SimpleWorker

logger = logging.getLogger(__name__)


def execute_run(run_id: str) -> dict:
    """
    Execute a test run. Called by the RQ worker for each job.

    RQ calls this function in a separate process, so we need to:
    1. Get the run from the in-memory store (passed via run_id)
    2. Run the async engine synchronously using asyncio.run()
    3. Return a summary dict (stored as the job result in Redis)

    Args:
        run_id: String UUID of the TestRun to execute

    Returns:
        dict with pass_rate and status for quick inspection
    """
    from uuid import UUID
    from app.runner.engine import run_test

    logger.info("Worker picked up run %s", run_id)

    run = store.get(UUID(run_id))
    if not run:
        logger.error("Run %s not found in store", run_id)
        return {"error": f"Run {run_id} not found"}

    try:
        # RQ workers are sync — run the async engine with asyncio.run()
        asyncio.run(run_test(run))

        logger.info(
            "Worker completed run %s — %d/%d passed",
            run_id,
            run.passed,
            run.total_scenarios,
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
        store.save(run)
        return {"run_id": run_id, "error": str(exc)}


if __name__ == "__main__":
    from redis import Redis
    from rq import Worker

    from app.core.config import settings

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    redis_conn = Redis.from_url(settings.REDIS_URL)
    worker = SimpleWorker(["agenteval"], connection=redis_conn)

    print(f"AgentEval worker starting — listening on queue 'agenteval'")
    print(f"Redis: {settings.REDIS_URL}")
    worker.work(with_scheduler=False)