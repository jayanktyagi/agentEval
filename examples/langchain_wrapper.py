"""
examples/langchain_wrapper.py

Thin FastAPI wrapper to connect a LangChain agent to AgentEval.

AgentEval sends tasks to your agent via HTTP POST.
This wrapper receives those requests and translates them
into LangChain agent calls, then returns the execution
trace in the format AgentEval expects.

Usage:
    pip install fastapi uvicorn langchain langchain-openai
    python examples/langchain_wrapper.py

Then point AgentEval at: http://localhost:9000/run
"""

import time
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import uvicorn

app = FastAPI(title="My LangChain Agent — AgentEval Wrapper")


# ---------------------------------------------------------------------------
# Define your actual tools here
# ---------------------------------------------------------------------------

@tool
def search_flights(origin: str, destination: str, date: str = "") -> dict:
    """Search for available flights between two cities."""
    # Replace with your real implementation
    return {"flights": [{"id": "FL001", "price": 150, "airline": "PIA"}]}


@tool
def check_availability(flight_id: str) -> dict:
    """Check seat availability for a specific flight."""
    # Replace with your real implementation
    return {"available": True, "seats": 10}


@tool
def book_ticket(flight_id: str, passenger_name: str) -> dict:
    """Book a ticket for a flight."""
    # Replace with your real implementation
    return {"booking_id": "BK001", "status": "confirmed"}


# ---------------------------------------------------------------------------
# Build the LangChain agent
# ---------------------------------------------------------------------------

tools = [search_flights, check_availability, book_ticket]

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful flight booking assistant. Use the available tools to complete booking tasks."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)


# ---------------------------------------------------------------------------
# AgentEval contract
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    task: str
    context: dict = {}


@app.post("/run")
async def run(request: AgentRequest) -> dict:
    """
    Receives a task from AgentEval, runs the LangChain agent,
    and returns the execution trace in AgentEval format.
    """
    tool_calls = []

    try:
        result = agent_executor.invoke({"input": request.task})

        # Parse intermediate steps into AgentEval tool call format
        for i, (action, observation) in enumerate(result.get("intermediate_steps", []), start=1):
            start = time.time()
            tool_calls.append({
                "tool_name": action.tool,
                "parameters": action.tool_input if isinstance(action.tool_input, dict) else {"input": action.tool_input},
                "response": observation,
                "status": "success",
                "duration_ms": int((time.time() - start) * 1000),
            })

        return {
            "tool_calls": tool_calls,
            "completed": True,
            "final_output": result.get("output", ""),
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