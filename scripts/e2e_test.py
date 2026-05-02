"""
scripts/e2e_test.py

End-to-end test script.

Sends a real AgentTest to the AgentEval API and polls until complete.
Run this after starting both servers:

    Terminal 1: python mock_agent/server.py
    Terminal 2: uvicorn backend.app.main:app --reload --port 8000
    Terminal 3: python scripts/e2e_test.py

What this tests:
- AgentEval API accepts a POST /runs request
- Background task runs the execution engine
- Engine calls the mock agent HTTP endpoint
- Trace is recorded correctly
- Pass/fail evaluation runs
- Results are readable via GET /runs/{run_id}
"""

import time
import httpx

AGENTEVAL_URL = "http://localhost:8000/api/v1"
MOCK_AGENT_URL = "http://localhost:9000/run"


def submit_run(name: str, task: str) -> str:
    """Submit a test run and return the run_id."""
    payload = {
        "name": name,
        "agent_endpoint": MOCK_AGENT_URL,
        "task_description": task,
        "expected_tools": ["search_flights", "check_availability", "book_ticket"],
        "max_steps": 10,
    }
    response = httpx.post(f"{AGENTEVAL_URL}/runs", json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["run_id"]


def poll_until_done(run_id: str, timeout: int = 30) -> dict:
    """Poll GET /runs/{run_id} until status is no longer 'running'."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = httpx.get(f"{AGENTEVAL_URL}/runs/{run_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["status"] != "running":
            return data
        time.sleep(0.5)
    raise TimeoutError(f"Run {run_id} did not complete within {timeout}s")


def print_run(run: dict) -> None:
    """Print a clean summary of a completed test run."""
    test = run["test"]
    print(f"\n{'='*55}")
    print(f"  {test['name']}")
    print(f"{'='*55}")
    print(f"  Status    : {run['status'].upper()}")
    print(f"  Passed    : {run['passed']}/{run['total_scenarios']}")
    print(f"  Pass rate : {run['pass_rate']:.0%}")
    print(f"{'='*55}")

    for result in run["results"]:
        scenario = result["scenario"]
        icon = "PASS" if result["status"] == "passed" else "FAIL"
        print(f"\n  [{icon}] {scenario['title']}")
        if result["status"] == "failed":
            print(f"         Reason : {result['failure_reason']}")
            print(f"         Detail : {result['failure_detail']}")
        print(f"         Tools  : {result['trace']['tool_calls'] and [c['tool_name'] for c in result['trace']['tool_calls']]}")
        print(f"         Steps  : {result['trace']['total_steps']}")
        print(f"         Accuracy : {result['tool_accuracy']:.0%}")

    print()


def run_scenario(name: str, task: str) -> None:
    print(f"\nSubmitting: {name}...")
    run_id = submit_run(name, task)
    print(f"Run ID: {run_id}")
    print("Polling for results", end="", flush=True)

    while True:
        response = httpx.get(f"{AGENTEVAL_URL}/runs/{run_id}", timeout=10)
        data = response.json()
        if data["status"] != "running":
            break
        print(".", end="", flush=True)
        time.sleep(0.5)

    print(" done.")
    print_run(data)


if __name__ == "__main__":
    print("\nAgentEval End-to-End Test")
    print("Make sure both servers are running before continuing.")
    print("  Mock agent : http://localhost:9000")
    print("  AgentEval  : http://localhost:8000")

    # Each task keyword triggers a different mock agent behavior
    scenarios = [
        ("Happy Path Agent",      "Book a happy flight from Karachi to Dubai"),
        ("Loop Agent",            "Book a loop flight from Karachi to Dubai"),
        ("Wrong Order Agent",     "Book a wrong flight from Karachi to Dubai"),
        ("Fail Agent",            "Book a fail flight from Karachi to Dubai"),
    ]

    for name, task in scenarios:
        try:
            run_scenario(name, task)
        except Exception as exc:
            print(f"  ERROR: {exc}")