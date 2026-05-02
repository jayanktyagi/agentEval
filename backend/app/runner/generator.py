"""
backend/app/runner/generator.py

Generates test scenarios using Groq (llama-3.3-70b-versatile).

Takes the developer's plain-English agent description and produces
10 structured TestScenario objects — 3 happy paths, 4 failure cases,
3 edge cases.

This is the only file that talks to an LLM. Everything else in the
system is completely unaware of which provider is being used.

If you want to swap to a different provider later, this is the
only file you need to change.

Get a free Groq API key at: console.groq.com
"""

import json
import logging

from groq import Groq

from app.core.config import settings
from app.models import ScenarioType, TestScenario

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert QA engineer specializing in AI agent testing.
Your job is to generate realistic, diverse test scenarios for an AI agent.

You must respond with valid JSON only. No explanation, no markdown, no code fences.
Just a raw JSON array."""


def build_prompt(
    task_description: str,
    expected_tools: list[str],
    max_steps: int,
) -> str:
    return f"""Generate exactly 10 test scenarios for the following AI agent:

Agent task: {task_description}
Available tools: {', '.join(expected_tools)}
Maximum allowed steps: {max_steps}

Return a JSON array of exactly 10 objects. Each object must have these fields:
- scenario_type: one of "happy_path", "failure_case", "edge_case"
- title: short human-readable title (max 60 chars)
- description: what this scenario is testing (1-2 sentences)
- task_prompt: the exact task string to send to the agent
- expected_tools: list of tool names expected to be called, in order
- expected_max_steps: integer, max steps before this scenario is a failure
- should_complete: boolean, whether the agent should signal task completion

Distribution: exactly 3 happy_path, 4 failure_case, 3 edge_case.

Happy path scenarios: well-formed tasks where the agent should succeed.
Failure case scenarios: missing info, bad input, or situations requiring error handling.
Edge case scenarios: unusual but valid inputs, boundary conditions, ambiguous tasks.

Make the task_prompt strings realistic and varied. Do not use placeholder text.
Make failure and edge case scenarios genuinely challenging.

Return only the JSON array. No other text."""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_scenarios(
    raw_json: str,
    fallback_tools: list[str],
    fallback_max_steps: int,
) -> list[TestScenario]:
    """
    Parse the LLM response into TestScenario objects.

    Handles cases where the model returns slightly malformed JSON
    by stripping common artifacts before parsing.
    """
    cleaned = raw_json.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

    data = json.loads(cleaned)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data)}")

    scenarios = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning("Skipping non-dict item at index %d", i)
            continue
        try:
            raw_type = item.get("scenario_type", "happy_path")
            try:
                scenario_type = ScenarioType(raw_type)
            except ValueError:
                scenario_type = ScenarioType.HAPPY_PATH

            scenario = TestScenario(
                scenario_type=scenario_type,
                title=item.get("title", f"Scenario {i + 1}"),
                description=item.get("description", ""),
                task_prompt=item.get("task_prompt", ""),
                expected_tools=item.get("expected_tools", fallback_tools),
                expected_max_steps=item.get("expected_max_steps", fallback_max_steps),
                should_complete=item.get("should_complete", True),
            )
            scenarios.append(scenario)
        except Exception as exc:
            logger.warning("Skipping malformed scenario %d: %s", i, exc)
            continue

    return scenarios


# ---------------------------------------------------------------------------
# Fallback — used when Groq call fails
# ---------------------------------------------------------------------------

def fallback_scenarios(
    task_description: str,
    expected_tools: list[str],
    max_steps: int,
) -> list[TestScenario]:
    """
    Returns 3 basic stub scenarios when the LLM call fails.
    Ensures the system always produces results even without a valid API key.
    """
    logger.warning("Using fallback stub scenarios — check your GROQ_API_KEY")
    return [
        TestScenario(
            scenario_type=ScenarioType.HAPPY_PATH,
            title="Happy path: standard execution",
            description="Agent receives a well-formed task and should complete it successfully.",
            task_prompt=task_description,
            expected_tools=expected_tools,
            expected_max_steps=max_steps,
            should_complete=True,
        ),
        TestScenario(
            scenario_type=ScenarioType.FAILURE_CASE,
            title="Failure case: missing required parameter",
            description="Task is underspecified — agent must handle gracefully.",
            task_prompt=f"{task_description} (details missing)",
            expected_tools=expected_tools[:1] if expected_tools else [],
            expected_max_steps=max_steps,
            should_complete=False,
        ),
        TestScenario(
            scenario_type=ScenarioType.EDGE_CASE,
            title="Edge case: ambiguous task",
            description="Task is valid but ambiguous — agent must clarify or make assumptions.",
            task_prompt=f"{task_description} sometime next week maybe",
            expected_tools=expected_tools,
            expected_max_steps=max_steps,
            should_complete=True,
        ),
    ]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def generate_scenarios(
    task_description: str,
    expected_tools: list[str],
    max_steps: int,
) -> list[TestScenario]:
    """
    Generate 10 test scenarios using Groq.

    Falls back to 3 stub scenarios if:
    - GROQ_API_KEY is not set
    - The API call fails
    - The response cannot be parsed
    """
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — using fallback scenarios")
        return fallback_scenarios(task_description, expected_tools, max_steps)

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        prompt = build_prompt(task_description, expected_tools, max_steps)

        logger.info("Generating scenarios via Groq for task: %s", task_description[:60])

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )

        raw = response.choices[0].message.content
        scenarios = parse_scenarios(raw, expected_tools, max_steps)

        if not scenarios:
            raise ValueError("Parsed 0 scenarios from Groq response")

        logger.info("Generated %d scenarios via Groq", len(scenarios))
        return scenarios

    except Exception as exc:
        logger.error("Groq scenario generation failed: %s", exc)
        return fallback_scenarios(task_description, expected_tools, max_steps)