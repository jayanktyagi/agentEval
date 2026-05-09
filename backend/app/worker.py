"""
backend/app/worker.py
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Windows event loop policy BEFORE anything else — module level
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger = logging.getLogger(__name__)


def execute_run(run_id: str) -> dict:
    logger.info("Worker picked up run %s", run_id)

    async def _execute():
        from uuid import UUID
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from app.core.config import settings
        from app.core.store import store
        from app.db.repository import get_run
        from app.runner.engine import run_test

        # Create fresh engine bound to THIS event loop
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        SessionFactory = async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        try:
            async with SessionFactory() as session:
                run = await get_run(session, UUID(run_id))

            if not run:
                logger.error("Run %s not found in Postgres", run_id)
                return {"error": f"Run {run_id} not found"}

            store.save(run)
            await run_test(run, session_factory=SessionFactory)

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
            return {"run_id": run_id, "error": str(exc)}
        finally:
            await engine.dispose()

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