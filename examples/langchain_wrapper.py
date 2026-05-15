"""
examples/langchain_wrapper.py

Thin FastAPI wrapper to connect a LangChain agent to AgentEval.
Uses LangGraph (LangChain v1.0+) -- AgentExecutor was removed in v1.0.

Usage:
    pip install fastapi uvicorn langgraph langchain-openai
    export OPENAI_API_KEY=your_key_here
    python examples/langchain_wrapper.py

Then point AgentEval at: http://localhost:9000/run
"""

import time
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
import uvicorn

app = FastAPI(title="My LangChain Agent -- AgentEval Wrapper")


# ---------------------------------------------------------------------------
# Define your actual tools here
# ---------------------------------------------------------------------------

@tool
def search_flights(origin: str, destination: str, date: str = "") -> dict:
    """Search for available flights between two cities."""
    return {"flights": [{"id": "FL001", "price": 150, "airline": "PIA"}]}


@tool
def check_availability(flight_id: str) -> dict:
    """Check seat availability for a specific flight."""
    return {"available": True, "seats": 10}


@tool
def book_ticket(flight_id: str, passenger_name: str) -> dict:
    """Book a ticket for a flight."""
    return {"booking_id": "BK001", "status": "confirmed"}


# ---------------------------------------------------------------------------
# Build the LangGraph agent
# ---------------------------------------------------------------------------

tools = [search_flights, check_availability, book_ticket]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_react_agent(llm, tools)


# ---------------------------------------------------------------------------
# AgentEval contract
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    task: str
    context: dict = {}


@app.post("/run")
async def run(request: AgentRequest) -> dict:
    """
    Receives a task from AgentEval, runs the LangGraph agent,
    and returns the execution trace in AgentEval format.
    """
    tool_calls = []

    try:
        result = agent.invoke({"messages": [("user", request.task)]})

        for message in result.get("messages", []):
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "tool_name": tc.get("name", "unknown"),
                        "parameters": tc.get("args", {}),
                        "response": {},
                        "status": "success",
                        "duration_ms": 0,
                    })

        final_output = ""
        if result.get("messages"):
            last = result["messages"][-1]
            if hasattr(last, "content"):
                final_output = last.content

        return {
            "tool_calls": tool_calls,
            "completed": True,
            "final_output": final_output,
        }

    except Exception as exc:
        return {
            "tool_calls": tool_calls,
            "completed": False,
            "final_output": str(exc),
        }


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "langchain"}


if __name__ == "__main__":
    uvicorn.run("langchain_wrapper:app", host="0.0.0.0", port=9000, reload=True)