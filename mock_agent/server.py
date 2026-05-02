"""
mock_agent/server.py

A fake agent server for testing AgentEval end-to-end locally.

It listens on http://localhost:9000/run and simulates four different
agent behaviors depending on what keyword appears in the task:

    "happy"   -> calls the right tools in the right order, completes
    "loop"    -> gets stuck calling the same tool repeatedly
    "wrong"   -> calls tools in the wrong order
    "fail"    -> times out / does not complete

If no keyword matches, defaults to happy path behavior.

Usage:
    python mock_agent/server.py

Then point AgentEval at: http://localhost:9000/run
"""

import random
import time

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AgentEval Mock Agent")


class AgentRequest(BaseModel):
    task: str
    context: dict = {}


# ---------------------------------------------------------------------------
# Behavior simulators
# ---------------------------------------------------------------------------

def happy_path(task: str) -> dict:
    """Calls the right tools in the right order and completes."""
    return {
        "tool_calls": [
            {
                "tool_name": "search_flights",
                "parameters": {"origin": "KHI", "destination": "DXB", "date": "2026-05-10"},
                "response": {"flights": [{"id": "PK301", "price": 150}]},
                "status": "success",
                "duration_ms": random.randint(80, 200),
            },
            {
                "tool_name": "check_availability",
                "parameters": {"flight_id": "PK301"},
                "response": {"available": True, "seats": 12},
                "status": "success",
                "duration_ms": random.randint(50, 120),
            },
            {
                "tool_name": "book_ticket",
                "parameters": {"flight_id": "PK301", "passenger": "Test User"},
                "response": {"booking_id": "BK9921", "status": "confirmed"},
                "status": "success",
                "duration_ms": random.randint(100, 300),
            },
        ],
        "completed": True,
        "final_output": "Flight PK301 booked successfully. Booking ID: BK9921.",
    }


def loop_behavior(task: str) -> dict:
    """Gets stuck calling the same tool with the same params repeatedly."""
    repeated_call = {
        "tool_name": "search_flights",
        "parameters": {"origin": "KHI", "destination": "DXB"},
        "response": {"flights": []},
        "status": "success",
        "duration_ms": 95,
    }
    return {
        "tool_calls": [repeated_call, repeated_call, repeated_call, repeated_call],
        "completed": False,
        "final_output": None,
    }


def wrong_order_behavior(task: str) -> dict:
    """Calls the right tools but in the wrong order."""
    return {
        "tool_calls": [
            {
                "tool_name": "book_ticket",
                "parameters": {"flight_id": "PK301"},
                "response": {"error": "flight not confirmed yet"},
                "status": "success",
                "duration_ms": 110,
            },
            {
                "tool_name": "search_flights",
                "parameters": {"origin": "KHI", "destination": "DXB"},
                "response": {"flights": [{"id": "PK301"}]},
                "status": "success",
                "duration_ms": 140,
            },
            {
                "tool_name": "check_availability",
                "parameters": {"flight_id": "PK301"},
                "response": {"available": True},
                "status": "success",
                "duration_ms": 90,
            },
        ],
        "completed": True,
        "final_output": "Booking attempted.",
    }


def fail_behavior(task: str) -> dict:
    """Starts but never completes — no completion signal."""
    return {
        "tool_calls": [
            {
                "tool_name": "search_flights",
                "parameters": {"origin": "KHI", "destination": "DXB"},
                "response": {"error": "upstream timeout"},
                "status": "failed",
                "duration_ms": 5000,
            },
        ],
        "completed": False,
        "final_output": None,
    }


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

BEHAVIORS = {
    "loop": loop_behavior,
    "wrong": wrong_order_behavior,
    "fail": fail_behavior,
    "happy": happy_path,
}


@app.post("/run")
async def run(request: AgentRequest) -> dict:
    task_lower = request.task.lower()

    handler = happy_path  # default
    for keyword, fn in BEHAVIORS.items():
        if keyword in task_lower:
            handler = fn
            break

    # Small simulated delay so it feels like a real agent
    time.sleep(0.1)

    return handler(request.task)


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "mock"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=9000, reload=True)