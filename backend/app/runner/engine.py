"""
backend/app/runner/engine.py

The test execution engine.

This is the core of AgentEval. It:
1. Takes a TestRun
2. Generates test scenarios (stub for now — LLM generation comes in Week 2)
3. Sends each scenario's task to the agent's HTTP endpoint
4. Records the full execution trace
5. Evaluates pass/fail
6. Updates the TestRun with results

The agent contract (what we expect from the agent's HTTP endpoint) is simple:

    POST {agent_endpoint}
    {
        "task": "Book a flight from Karachi to Dubai",
        "context": {}
    }

    Response:
    {
        "tool_calls": [
            {
                "tool_name": "search_flights",
                "parameters": {"origin": "KHI", "destination": "DXB"},
                "response": {...},
                "status": "success",
                "duration_ms": 120
            }
        ],
        "completed": true,
        "final_output": "Flight booked successfully."
    }
"""

import asyncio
import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.core.store import store
from app.models import (
    ExecutionTrace,
    FailureReason,
    ScenarioResult,
    ScenarioType,
    StepStatus,
    TestRun,
    TestScenario,
    TestStatus,
    ToolCall,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scenario generation (stub — replaced by LLM in Week 2)
# ---------------------------------------------------------------------------

def generate_stub_scenarios(run: TestRun) -> list[TestScenario]:
    """
    Generate placeholder test scenarios.

    In Week 2 this gets replaced by LLM-based generation via Claude API.
    For now we produce 3 stubs so the full pipeline can be tested end-to-end.
    """
    task = run.test.task_description
    tools = run.test.expected_tools
    max_steps = run.test.max_steps

    return [
        TestScenario(
            scenario_type=ScenarioType.HAPPY_PATH,
            title="Happy path: standard execution",
            description="Agent receives a well-formed task and should complete it successfully.",
            task_prompt=task,
            expected_tools=tools,
            expected_max_steps=max_steps,
            should_complete=True,
        ),
        TestScenario(
            scenario_type=ScenarioType.FAILURE_CASE,
            title="Failure case: missing required parameter",
            description="Task is underspecified — agent must handle gracefully.",
            task_prompt=f"{task} (no date specified)",
            expected_tools=tools[:1] if tools else [],
            expected_max_steps=max_steps,
            should_complete=False,
        ),
        TestScenario(
            scenario_type=ScenarioType.EDGE_CASE,
            title="Edge case: impossible task",
            description="Task cannot be completed — agent should recognize and exit cleanly.",
            task_prompt=f"{task} for a date that does not exist",
            expected_tools=[],
            expected_max_steps=3,
            should_complete=False,
        ),
    ]


# ---------------------------------------------------------------------------
# Agent communication
# ---------------------------------------------------------------------------

async def call_agent(endpoint: str, task: str, timeout: int) -> dict | None:
    """
    Send a task to the agent's HTTP endpoint and return the raw response dict.
    Returns None if the call fails or times out.
    """
    payload = {"task": task, "context": {}}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.warning("Agent timed out for task: %s", task[:80])
        return None
    except httpx.HTTPStatusError as exc:
        logger.warning("Agent returned HTTP %s for task: %s", exc.response.status_code, task[:80])
        return None
    except Exception as exc:
        logger.error("Unexpected error calling agent: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Trace parsing
# ---------------------------------------------------------------------------

def parse_trace(raw: dict, task: str) -> ExecutionTrace:
    """Parse the agent's raw response into a structured ExecutionTrace."""
    tool_calls = []

    for i, raw_call in enumerate(raw.get("tool_calls", []), start=1):
        tool_calls.append(
            ToolCall(
                step=i,
                tool_name=raw_call.get("tool_name", "unknown"),
                parameters=raw_call.get("parameters", {}),
                response=raw_call.get("response"),
                status=raw_call.get("status", StepStatus.SUCCESS),
                duration_ms=raw_call.get("duration_ms", 0),
            )
        )

    # Loop detection: same tool called with identical parameters 3+ times
    loop_detected = False
    loop_at_step = None
    seen: dict[str, int] = {}

    for call in tool_calls:
        key = f"{call.tool_name}:{sorted(call.parameters.items())}"
        seen[key] = seen.get(key, 0) + 1
        if seen[key] >= 3 and not loop_detected:
            loop_detected = True
            loop_at_step = call.step

    return ExecutionTrace(
        task=task,
        tool_calls=tool_calls,
        total_steps=len(tool_calls),
        completed=raw.get("completed", False),
        loop_detected=loop_detected,
        loop_at_step=loop_at_step,
        final_output=raw.get("final_output"),
        finished_at=datetime.utcnow(),
    )


def empty_trace(task: str) -> ExecutionTrace:
    """Return an empty trace for when the agent call fails entirely."""
    return ExecutionTrace(
        task=task,
        tool_calls=[],
        total_steps=0,
        completed=False,
        finished_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Pass/fail evaluation
# ---------------------------------------------------------------------------

def evaluate(scenario: TestScenario, trace: ExecutionTrace) -> ScenarioResult:
    """
    Determine whether a scenario passed or failed.

    Rules (checked in order — first failure wins):
    1. If the agent call failed entirely -> AGENT_ERROR
    2. If a loop was detected -> LOOP
    3. If exceeded max steps -> EXCEEDED_STEPS
    4. If should_complete=True but agent did not complete -> NO_COMPLETION
    5. If expected tools were not all called -> WRONG_TOOL
    6. If tools were called in wrong order -> WRONG_ORDER
    7. Otherwise -> PASSED
    """
    actual_tools = trace.tool_sequence()
    expected_tools = scenario.expected_tools

    # Tool accuracy: what fraction of expected tools appeared in the trace
    if expected_tools:
        called_set = set(actual_tools)
        expected_set = set(expected_tools)
        tool_accuracy = len(called_set & expected_set) / len(expected_set)
    else:
        tool_accuracy = 1.0 if not actual_tools else 0.5

    # Step efficiency: ratio of expected to actual (capped at 1.0)
    if trace.total_steps > 0:
        step_efficiency = min(1.0, scenario.expected_max_steps / trace.total_steps)
    else:
        step_efficiency = 0.0

    def fail(reason: FailureReason, detail: str, step: int | None = None) -> ScenarioResult:
        return ScenarioResult(
            scenario=scenario,
            trace=trace,
            status=TestStatus.FAILED,
            failure_reason=reason,
            failure_at_step=step,
            failure_detail=detail,
            tool_accuracy=tool_accuracy,
            step_efficiency=step_efficiency,
        )

    def passed() -> ScenarioResult:
        return ScenarioResult(
            scenario=scenario,
            trace=trace,
            status=TestStatus.PASSED,
            tool_accuracy=tool_accuracy,
            step_efficiency=step_efficiency,
        )

    # Rule 1: empty trace means the HTTP call failed
    if trace.total_steps == 0 and not trace.completed:
        return fail(FailureReason.AGENT_ERROR, "Agent did not respond or returned an error")

    # Rule 2: loop
    if trace.loop_detected:
        return fail(
            FailureReason.LOOP,
            f"Loop detected at step {trace.loop_at_step} — same tool called 3+ times with identical params",
            step=trace.loop_at_step,
        )

    # Rule 3: exceeded max steps
    if trace.total_steps > scenario.expected_max_steps:
        return fail(
            FailureReason.EXCEEDED_STEPS,
            f"Used {trace.total_steps} steps, max allowed is {scenario.expected_max_steps}",
        )

    # Rule 4: completion expectation
    if scenario.should_complete and not trace.completed:
        return fail(FailureReason.NO_COMPLETION, "Agent did not signal task completion")

    # Rule 5: wrong tools (only check if we had expectations)
    if expected_tools:
        missing = [t for t in expected_tools if t not in set(actual_tools)]
        if missing:
            return fail(
                FailureReason.WRONG_TOOL,
                f"Expected tools not called: {', '.join(missing)}",
            )

    # Rule 6: wrong order (only meaningful if all expected tools were called)
    if expected_tools and len(actual_tools) >= len(expected_tools):
        actual_order = [t for t in actual_tools if t in set(expected_tools)]
        if actual_order != expected_tools:
            first_wrong = next(
                (i + 1 for i, (a, e) in enumerate(zip(actual_order, expected_tools)) if a != e),
                None,
            )
            return fail(
                FailureReason.WRONG_ORDER,
                f"Tools called in wrong order. Expected {expected_tools}, got {actual_order}",
                step=first_wrong,
            )

    return passed()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def run_test(run: TestRun) -> None:
    """
    Execute all scenarios for a TestRun.

    Called as a FastAPI background task from POST /runs.
    Updates the run in-place and saves to store after each scenario completes.
    """
    logger.info("Starting test run %s for agent: %s", run.run_id, run.test.agent_endpoint)

    scenarios = generate_stub_scenarios(run)
    run.scenarios = scenarios
    results = []

    for scenario in scenarios:
        logger.info("Running scenario: %s", scenario.title)

        raw = await call_agent(
            endpoint=run.test.agent_endpoint,
            task=scenario.task_prompt,
            timeout=run.test.timeout_seconds,
        )

        trace = parse_trace(raw, scenario.task_prompt) if raw else empty_trace(scenario.task_prompt)
        result = evaluate(scenario, trace)
        results.append(result)

        # Persist after each scenario so partial results are always readable
        run.results = results
        store.save(run)

        # Small delay between scenarios — be polite to the agent under test
        await asyncio.sleep(0.5)

    run.results = results
    run.compute_metrics()
    store.save(run)

    logger.info(
        "Test run %s complete — %d/%d passed (%.0f%%)",
        run.run_id,
        run.passed,
        run.total_scenarios,
        run.pass_rate * 100,
    )