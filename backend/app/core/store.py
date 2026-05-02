"""
backend/app/core/store.py

In-memory store for test runs.

This is intentionally simple — a plain dict.
In Week 2 we replace this with PostgreSQL via SQLAlchemy.
The rest of the app talks to this interface, so swapping the
backing store requires zero changes elsewhere.
"""

from uuid import UUID

from app.models import TestRun


class InMemoryStore:
    def __init__(self):
        self._runs: dict[UUID, TestRun] = {}

    def save(self, run: TestRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: UUID) -> TestRun | None:
        return self._runs.get(run_id)

    def all(self) -> list[TestRun]:
        return list(self._runs.values())


# Single instance — imported wherever needed
store = InMemoryStore()