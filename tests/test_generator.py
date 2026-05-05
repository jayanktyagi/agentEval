"""
tests/test_generator.py

Tests for the Groq scenario generator.

Uses mocking so these run without a real API key.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models import ScenarioType
from app.runner.generator import fallback_scenarios, parse_scenarios


VALID_GROQ_RESPONSE = json.dumps([
    {
        "scenario_type": "happy_path",
        "title": "Happy path: successful flight booking",
        "description": "Agent books a flight with all required info provided.",
        "task_prompt": "Book a flight from Karachi to Dubai on May 10th",
        "expected_tools": ["search_flights", "check_availability", "book_ticket"],
        "expected_max_steps": 5,
        "should_complete": True,
    },
    {
        "scenario_type": "failure_case",
        "title": "Failure case: no date provided",
        "description": "Agent must handle missing date gracefully.",
        "task_prompt": "Book a flight from Karachi to Dubai",
        "expected_tools": ["search_flights"],
        "expected_max_steps": 3,
        "should_complete": False,
    },
    {
        "scenario_type": "edge_case",
        "title": "Edge case: same origin and destination",
        "description": "Agent receives an impossible route.",
        "task_prompt": "Book a flight from Karachi to Karachi",
        "expected_tools": [],
        "expected_max_steps": 2,
        "should_complete": False,
    },
])


class TestParseScenarios:
    def test_parses_valid_response(self):
        scenarios = parse_scenarios(VALID_GROQ_RESPONSE, ["search_flights"], 10)
        assert len(scenarios) == 3

    def test_correct_types(self):
        scenarios = parse_scenarios(VALID_GROQ_RESPONSE, [], 10)
        types = [s.scenario_type for s in scenarios]
        assert ScenarioType.HAPPY_PATH in types
        assert ScenarioType.FAILURE_CASE in types
        assert ScenarioType.EDGE_CASE in types

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{VALID_GROQ_RESPONSE}\n```"
        scenarios = parse_scenarios(fenced, [], 10)
        assert len(scenarios) == 3

    def test_skips_malformed_items(self):
        data = json.dumps([
            {
                "scenario_type": "happy_path",
                "title": "Good scenario",
                "description": "Works fine",
                "task_prompt": "Do something",
                "expected_tools": ["tool_a"],
                "expected_max_steps": 5,
                "should_complete": True,
            },
            "this is not a dict and should be skipped",
        ])
        scenarios = parse_scenarios(data, [], 10)
        assert len(scenarios) == 1

    def test_unknown_scenario_type_defaults_to_happy_path(self):
        data = json.dumps([{
            "scenario_type": "made_up_type",
            "title": "Unknown type",
            "description": "Test",
            "task_prompt": "Do something",
            "expected_tools": [],
            "expected_max_steps": 5,
            "should_complete": True,
        }])
        scenarios = parse_scenarios(data, [], 10)
        assert scenarios[0].scenario_type == ScenarioType.HAPPY_PATH


class TestFallbackScenarios:
    def test_returns_three_scenarios(self):
        result = fallback_scenarios("Book a flight", ["search_flights"], 10)
        assert len(result) == 3

    def test_has_one_of_each_type(self):
        result = fallback_scenarios("Book a flight", ["search_flights"], 10)
        types = [s.scenario_type for s in result]
        assert ScenarioType.HAPPY_PATH in types
        assert ScenarioType.FAILURE_CASE in types
        assert ScenarioType.EDGE_CASE in types

    def test_uses_provided_task(self):
        result = fallback_scenarios("Book a hotel", ["search_hotels"], 5)
        assert "Book a hotel" in result[0].task_prompt


class TestGenerateScenarios:
    @pytest.mark.asyncio
    async def test_falls_back_when_no_api_key(self):
        with patch("app.runner.generator.settings") as mock_settings:
            mock_settings.GROQ_API_KEY = ""
            from app.runner.generator import generate_scenarios
            result = await generate_scenarios("Book a flight", ["search_flights"], 10)
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_uses_groq_when_key_present(self):
        mock_choice = MagicMock()
        mock_choice.message.content = VALID_GROQ_RESPONSE

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("app.runner.generator.settings") as mock_settings, \
             patch("app.runner.generator.Groq") as mock_groq:
            mock_settings.GROQ_API_KEY = "fake-key-for-testing"
            mock_groq.return_value = mock_client

            from app.runner.generator import generate_scenarios
            result = await generate_scenarios("Book a flight", ["search_flights"], 10)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_falls_back_on_api_error(self):
        with patch("app.runner.generator.settings") as mock_settings, \
             patch("app.runner.generator.Groq") as mock_groq:
            mock_settings.GROQ_API_KEY = "fake-key"
            mock_groq.side_effect = Exception("API error")

            from app.runner.generator import generate_scenarios
            result = await generate_scenarios("Book a flight", ["search_flights"], 10)

        assert len(result) >= 1