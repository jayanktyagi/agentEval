"""
backend/app/db/orm.py

SQLAlchemy ORM table definitions.

We store TestRun and ScenarioResult as JSON columns for simplicity.
This means we don't need a complex schema with foreign keys for the MVP —
just two tables that store structured JSON blobs.

This is a deliberate tradeoff: faster to build, easy to query for the
dashboard, and simple to evolve. If we need relational queries later
we can migrate.

Tables:
    test_runs         — one row per TestRun
    scenario_results  — one row per ScenarioResult, linked to a test_run
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class TestRunORM(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    task_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")

    # Aggregate metrics
    total_scenarios: Mapped[int] = mapped_column(default=0)
    passed: Mapped[int] = mapped_column(default=0)
    failed: Mapped[int] = mapped_column(default=0)
    pass_rate: Mapped[float] = mapped_column(default=0.0)

    # Full run data stored as JSON for easy retrieval
    test_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationship to results
    results: Mapped[list["ScenarioResultORM"]] = relationship(
        "ScenarioResultORM",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class ScenarioResultORM(Base):
    __tablename__ = "scenario_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
    )

    scenario_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_at_step: Mapped[int | None] = mapped_column(nullable=True)

    tool_accuracy: Mapped[float] = mapped_column(default=0.0)
    step_efficiency: Mapped[float] = mapped_column(default=0.0)
    total_steps: Mapped[int] = mapped_column(default=0)

    # Full scenario and trace stored as JSON
    scenario_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    trace_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    run: Mapped["TestRunORM"] = relationship("TestRunORM", back_populates="results")