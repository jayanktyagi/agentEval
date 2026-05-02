"""
tests/test_engine.py

Tests for the pass/fail evaluation logic.
Run with: pytest tests/
"""

import pytest

from app.models import (
    ExecutionTrace,
    ScenarioType,
    StepStatus,
    TestScenario,
    TestStatus,
    ToolCall,
)
from app.runner.engine import empty_trace, evaluate, parse_trace


def make_scenario(
    expected_tools: list[str],
    max_steps: int = 10,
    should_complete: bool = True,
    scenario_type: ScenarioType = ScenarioType.HAPPY_PATH,
) -> TestScenario:
    return TestScenario(
        scenario_type=scenario_type,
        title="Test scenario",
        description="Test",
        task_prompt="Do a thing",
        expected_tools=expected_tools,
        expected_max_steps=max_steps,
        should_complete=should_complete,
    )


def make_trace(
    tools: list[str],
    completed: bool = True,
    loop_detected: bool = False,
    loop_at_step: int | None = None,
) -> ExecutionTrace:
    calls = [
        ToolCall(step=i + 1, tool_name=name, parameters={}, response=None, status=StepStatus.SUCCESS)
        for i, name in enumerate(tools)
    ]
    return ExecutionTrace(
        task="Do a thing",
        tool_calls=calls,
        total_steps=len(calls),
        completed=completed,
        loop_detected=loop_detected,
        loop_at_step=loop_at_step,
    )


class TestEvaluateHappyPath:
    def test_passes_when_everything_correct(self):
        scenario = make_scenario(["search", "book"])
        trace = make_trace(["search", "book"], completed=True)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.PASSED

    def test_passes_with_extra_tools_not_in_expected(self):
        scenario = make_scenario(["search", "book"])
        trace = make_trace(["search", "check", "book"], completed=True)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.PASSED


class TestEvaluateFailures:
    def test_fails_on_empty_trace(self):
        scenario = make_scenario(["search"])
        trace = empty_trace("Do a thing")
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED

    def test_fails_on_loop(self):
        scenario = make_scenario(["search", "book"])
        trace = make_trace(["search", "book"], completed=False, loop_detected=True, loop_at_step=3)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED
        assert result.failure_reason == "loop_detected"

    def test_fails_when_exceeds_max_steps(self):
        scenario = make_scenario(["search"], max_steps=2)
        trace = make_trace(["search", "check", "book"], completed=True)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED
        assert result.failure_reason == "exceeded_steps"

    def test_fails_when_should_complete_but_did_not(self):
        scenario = make_scenario(["search"], should_complete=True)
        trace = make_trace(["search"], completed=False)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED
        assert result.failure_reason == "no_completion"

    def test_fails_when_wrong_tool_called(self):
        scenario = make_scenario(["search", "book"])
        trace = make_trace(["search", "cancel"], completed=True)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED
        assert result.failure_reason == "wrong_tool"

    def test_fails_when_tools_called_out_of_order(self):
        scenario = make_scenario(["search", "check", "book"])
        trace = make_trace(["check", "search", "book"], completed=True)
        result = evaluate(scenario, trace)
        assert result.status == TestStatus.FAILED
        assert result.failure_reason == "wrong_order"


class TestParseTrace:
    def test_parses_tool_calls(self):
        raw = {
            "tool_calls": [
                {"tool_name": "search_flights", "parameters": {"origin": "KHI"}, "response": {}, "status": "success", "duration_ms": 100},
                {"tool_name": "book_ticket", "parameters": {}, "response": {}, "status": "success", "duration_ms": 200},
            ],
            "completed": True,
            "final_output": "Done",
        }
        trace = parse_trace(raw, "Book a flight")
        assert trace.total_steps == 2
        assert trace.tool_sequence() == ["search_flights", "book_ticket"]
        assert trace.completed is True

    def test_detects_loop(self):
        raw = {
            "tool_calls": [
                {"tool_name": "search", "parameters": {"q": "same"}, "response": {}, "status": "success", "duration_ms": 10},
                {"tool_name": "search", "parameters": {"q": "same"}, "response": {}, "status": "success", "duration_ms": 10},
                {"tool_name": "search", "parameters": {"q": "same"}, "response": {}, "status": "success", "duration_ms": 10},
            ],
            "completed": False,
        }
        trace = parse_trace(raw, "Search for something")
        assert trace.loop_detected is True
        assert trace.loop_at_step == 3