"""
backend/app/core/queue.py

Redis job queue setup using RQ (Redis Queue).

RQ is the simplest Python job queue. It uses Redis as a broker
and runs jobs in a separate worker process.

Why RQ over Celery:
- Much simpler to set up and understand
- No separate broker config needed — just Redis
- Perfect for our scale at MVP
- Easy to swap out later if needed

Usage:
    from app.core.queue import enqueue_run
    enqueue_run(run)
"""

import logging

from redis import Redis
from rq import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------

def get_redis() -> Redis:
    """Return a Redis connection using the URL from settings."""
    return Redis.from_url(settings.REDIS_URL)


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------

def get_queue() -> Queue:
    """Return the main AgentEval job queue."""
    return Queue("agenteval", connection=get_redis())


# ---------------------------------------------------------------------------
# Enqueue a test run
# ---------------------------------------------------------------------------

def enqueue_run(run_id: str) -> None:
    """
    Push a test run onto the Redis queue.

    The worker picks this up and calls execute_run(run_id).
    We pass only the run_id — the worker fetches the full
    run from Postgres so we don't serialize large objects.

    Args:
        run_id: The UUID of the TestRun to execute (as string)
    """
    try:
        queue = get_queue()
        job = queue.enqueue(
            "app.worker.execute_run",
            run_id,
            job_timeout=300,      # 5 minute max per run
            result_ttl=86400,     # keep result for 24 hours
        )
        logger.info("Enqueued run %s as job %s", run_id, job.id)
    except Exception as exc:
        logger.error("Failed to enqueue run %s: %s", run_id, exc)
        raise