"""
agenteval/models.py

Core data structures for AgentEval.
This is the schema everything else is built around.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ScenarioType(str, Enum):
    HAPPY_PATH = "happy_path"
    FAILURE_CASE = "failure_case"
    EDGE_CASE = "edge_case"


class StepStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    LOOP_DETECTED = "loop_detected"


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    RUNNING = "running"


# ---------------------------------------------------------------------------
# Tool Call — one action the agent took
# ---------------------------------------------------------------------------

class ToolCall(BaseModel):
    """A single tool invocation recorded during agent execution."""

    step: int = Field(..., description="Step number in the execution trace (1-indexed)")
    tool_name: str = Field(..., description="Name of the tool the agent called")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters passed to the tool")
    response: Any = Field(default=None, description="What the tool returned")
    status: StepStatus = Field(default=StepStatus.SUCCESS)
    duration_ms: int = Field(default=0, description="How long this tool call took in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


# ---------------------------------------------------------------------------
# Execution Trace — the full recording of one agent run
# ---------------------------------------------------------------------------

class ExecutionTrace(BaseModel):
    """Complete recording of one agent task execution."""

    trace_id: UUID = Field(default_factory=uuid4)
    task: str = Field(..., description="The task that was sent to the agent")
    tool_calls: list[ToolCall] = Field(default_factory=list)
    total_steps: int = Field(default=0)
    completed: bool = Field(default=False, description="Did the agent signal task completion?")
    loop_detected: bool = Field(default=False)
    loop_at_step: int | None = Field(default=None, description="Step where loop was first detected")
    final_output: str | None = Field(default=None, description="Agent's final response text")
    total_duration_ms: int = Field(default=0)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)

    def tool_sequence(self) -> list[str]:
        """Return just the ordered list of tool names called."""
        return [call.tool_name for call in self.tool_calls]


# ---------------------------------------------------------------------------
# Test Scenario — one test case
# ---------------------------------------------------------------------------

class TestScenario(BaseModel):
    """A single test scenario generated for the agent."""

    scenario_id: UUID = Field(default_factory=uuid4)
    scenario_type: ScenarioType
    title: str = Field(..., description="Short human-readable title, e.g. 'Happy path: successful booking'")
    description: str = Field(..., description="What this scenario is testing")
    task_prompt: str = Field(..., description="The actual task string sent to the agent")
    expected_tools: list[str] = Field(..., description="Tools expected to be called, in order")
    expected_max_steps: int = Field(..., description="Maximum steps before we consider it a failure")
    should_complete: bool = Field(default=True, description="Should the agent signal task completion?")

    class Config:
        use_enum_values = True


# ---------------------------------------------------------------------------
# Scenario Result — outcome of running one scenario
# ---------------------------------------------------------------------------

class FailureReason(str, Enum):
    WRONG_TOOL = "wrong_tool"
    WRONG_ORDER = "wrong_order"
    EXCEEDED_STEPS = "exceeded_steps"
    LOOP = "loop_detected"
    NO_COMPLETION = "no_completion"
    AGENT_ERROR = "agent_error"
    TIMEOUT = "timeout"


class ScenarioResult(BaseModel):
    """The pass/fail outcome of running a single test scenario."""

    result_id: UUID = Field(default_factory=uuid4)
    scenario: TestScenario
    trace: ExecutionTrace
    status: TestStatus

    # Detailed failure info
    failure_reason: FailureReason | None = Field(default=None)
    failure_at_step: int | None = Field(default=None, description="Which step caused the failure")
    failure_detail: str | None = Field(default=None, description="Human-readable explanation of what went wrong")

    # Metrics
    tool_accuracy: float = Field(
        default=0.0,
        description="Fraction of expected tools that were actually called (0.0–1.0)"
    )
    step_efficiency: float = Field(
        default=0.0,
        description="Ratio of expected steps to actual steps. 1.0 = perfect, <1.0 = used more steps"
    )

    class Config:
        use_enum_values = True

    def passed(self) -> bool:
        return self.status == TestStatus.PASSED


# ---------------------------------------------------------------------------
# AgentTest — the top-level object a developer creates
# ---------------------------------------------------------------------------

class AgentTest(BaseModel):
    """
    The primary configuration object for a test run.

    This is what the developer defines. Everything else flows from it.

    Example:
        test = AgentTest(
            name="Flight Booking Agent",
            agent_endpoint="http://localhost:8000/run",
            task_description="Book a flight from Karachi to Dubai for next Friday",
            expected_tools=["search_flights", "check_availability", "book_ticket"],
            max_steps=10,
        )
    """

    test_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Human-readable name for this test suite")
    agent_endpoint: str = Field(..., description="HTTP endpoint AgentEval will POST tasks to")
    task_description: str = Field(
        ...,
        description="Plain English description of what the agent is supposed to do"
    )
    expected_tools: list[str] = Field(
        ...,
        description="List of tools the agent has access to and is expected to use"
    )
    max_steps: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum allowed steps per scenario before marking as failure"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Max seconds to wait for agent response per step"
    )
    tags: list[str] = Field(default_factory=list, description="Optional tags for filtering/grouping")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# TestRun — the result of executing a full AgentTest
# ---------------------------------------------------------------------------

class TestRun(BaseModel):
    """The complete result of running all scenarios for an AgentTest."""

    run_id: UUID = Field(default_factory=uuid4)
    test: AgentTest
    scenarios: list[TestScenario] = Field(default_factory=list)
    results: list[ScenarioResult] = Field(default_factory=list)
    status: TestStatus = Field(default=TestStatus.RUNNING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)

    # Aggregate metrics — computed after all scenarios run
    total_scenarios: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    pass_rate: float = Field(default=0.0, description="Fraction of scenarios that passed (0.0–1.0)")

    class Config:
        use_enum_values = True

    def compute_metrics(self) -> None:
        """Recompute aggregate metrics from results. Call after all scenarios finish."""
        self.total_scenarios = len(self.results)
        self.passed = sum(1 for r in self.results if r.passed())
        self.failed = self.total_scenarios - self.passed
        self.pass_rate = self.passed / self.total_scenarios if self.total_scenarios > 0 else 0.0
        self.finished_at = datetime.utcnow()
        self.status = TestStatus.PASSED if self.failed == 0 else TestStatus.FAILED

    def summary(self) -> str:
        """Pretty-print a summary of the test run."""
        lines = [
            f"\n{'='*50}",
            f"  AgentEval — {self.test.name}",
            f"{'='*50}",
            f"  ✅ Passed : {self.passed}/{self.total_scenarios}",
            f"  ❌ Failed : {self.failed}/{self.total_scenarios}",
            f"  Pass Rate: {self.pass_rate:.0%}",
            f"{'='*50}",
        ]
        if self.failed > 0:
            lines.append("\n  Failure breakdown:")
            for r in self.results:
                if not r.passed():
                    lines.append(
                        f"  - {r.scenario.title}: {r.failure_detail or r.failure_reason}"
                    )
        lines.append("")
        return "\n".join(lines)