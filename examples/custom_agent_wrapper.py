"""
examples/custom_agent_wrapper.py

Thin FastAPI wrapper for any custom Python agent.

If your agent is not built with LangChain or CrewAI,
use this template. Just replace the tool functions
with your actual implementation.

Usage:
    pip install fastapi uvicorn
    python examples/custom_agent_wrapper.py

Then point AgentEval at: http://localhost:9000/run
"""

import time
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="My Custom Agent — AgentEval Wrapper")


# ---------------------------------------------------------------------------
# Your actual tool implementations
# ---------------------------------------------------------------------------

def search_flights(origin: str, destination: str, date: str = "") -> dict:
    # Replace with your real implementation
    return {"flights": [{"id": "FL001", "price": 150}]}


def check_availability(flight_id: str) -> dict:
    # Replace with your real implementation
    return {"available": True, "seats": 10}


def book_ticket(flight_id: str, passenger_name: str = "Passenger") -> dict:
    # Replace with your real implementation
    return {"booking_id": "BK001", "status": "confirmed"}


TOOLS = {
    "search_flights": search_flights,
    "check_availability": check_availability,
    "book_ticket": book_ticket,
}


# ---------------------------------------------------------------------------
# Your agent logic
# ---------------------------------------------------------------------------

def run_agent(task: str) -> tuple[list[dict], bool, str]:
    """
    Run your agent on a task.

    Returns:
        tool_calls: list of tool calls made
        completed: whether the agent completed the task
        final_output: agent's final response
    """
    tool_calls = []

    # Replace this with your actual agent logic.
    # This example shows the expected format AgentEval needs.

    # Example: simple sequential execution
    steps = [
        ("search_flights", {"origin": "KHI", "destination": "DXB", "date": "2026-05-10"}),
        ("check_availability", {"flight_id": "FL001"}),
        ("book_ticket", {"flight_id": "FL001", "passenger_name": "Test User"}),
    ]

    for tool_name, params in steps:
        start = time.time()
        try:
            tool_fn = TOOLS[tool_name]
            response = tool_fn(**params)
            status = "success"
        except Exception as exc:
            response = {"error": str(exc)}
            status = "failed"

        tool_calls.append({
            "tool_name": tool_name,
            "parameters": params,
            "response": response,
            "status": status,
            "duration_ms": int((time.time() - start) * 1000),
        })

    return tool_calls, True, "Task completed successfully"


# ---------------------------------------------------------------------------
# AgentEval contract — do not change this part
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    task: str
    context: dict = {}


@app.post("/run")
async def run(request: AgentRequest) -> dict:
    tool_calls, completed, final_output = run_agent(request.task)
    return {
        "tool_calls": tool_calls,
        "completed": completed,
        "final_output": final_output,
    }


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "custom"}


if __name__ == "__main__":
    uvicorn.run("custom_agent_wrapper:app", host="0.0.0.0", port=9000, reload=True)