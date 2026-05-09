<div align="center">

# AgentEval

![Demo](docs/demo.gif)

**The missing test framework for AI agents.**

[![CI](https://github.com/Fizza-Mukhtar/agentEval/actions/workflows/ci.yml/badge.svg)](https://github.com/Fizza-Mukhtar/agentEval/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

<p align="center"><i>Because guessing whether your agent works is not good enough.</i></p>

</div>

---

## The Problem

Every developer is building AI agents. Nobody is testing them properly.

Tools like LangSmith and Confident AI check whether an LLM's **text output** was accurate. But your agent doesn't just generate text — it **takes actions**: calling tools, querying databases, browsing the web, sending emails.

What happens when it calls the wrong tool at step 3? What happens when it loops forever? What happens when a new deployment silently breaks a workflow that was working yesterday?

**You don't know. That's the problem.**

According to Carnegie Mellon research, leading AI agents successfully complete only **30–35% of multi-step tasks**. That means in 65–70% of cases — the agent fails, and you have no visibility into where or why.

AgentEval fixes this.

---

## What AgentEval Does

| What existing tools test | What AgentEval tests |
|---|---|
| Was the LLM response accurate? | Was the **right tool** called? |
| Was the output well-formatted? | Were steps executed in the **correct sequence**? |
| — | Did the agent **recover from failures**? |
| — | Did it complete within the **expected step count**? |
| — | What **regressed** after your last deploy? |

---

## Quick Start

**1. Clone and install:**
```bash
git clone https://github.com/Fizza-Mukhtar/agentEval
cd agenteval
pip install -r requirements.txt
```

**2. Set up environment:**
```bash
cp .env.example .env
# Add your GROQ_API_KEY — free at console.groq.com
```

**3. Start infrastructure:**
```bash
docker compose up -d db redis
```

**4. Start the API and worker:**
```bash
# Terminal 1
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2
cd backend && python -m app.worker
```

**5. Run your first test:**
```bash
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Flight Agent",
    "agent_endpoint": "http://localhost:9000/run",
    "task_description": "Book a flight from Karachi to Dubai",
    "expected_tools": ["search_flights", "check_availability", "book_ticket"],
    "max_steps": 10
  }'
```

**6. Check results:**
```bash
curl http://localhost:8000/api/v1/runs/{run_id}
```

---

## Testing with the Mock Agent

No agent yet? Use the built-in mock agent to try AgentEval end-to-end:

```bash
# Terminal 3
python mock_agent/server.py  # runs on port 9001

# Terminal 4
python scripts/e2e_test.py
```

The mock agent simulates 4 behaviors — happy path, loop, wrong order, and failure — triggered by keywords in the task prompt.

---

## Windows Setup

**Postgres port conflict:** If you have Postgres installed locally, Docker's Postgres conflicts on port 5432. The `docker-compose.yml` uses port `5433`. Make sure your `.env` has:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/agenteval
```

**ClickHouse port conflict:** If you have ClickHouse installed, it occupies port 9000. The mock agent runs on port `9001` instead:

```bash
python mock_agent/server.py  # listens on port 9001
```

Use `http://localhost:9001/run` as the agent endpoint when testing locally on Windows.

---

## Project Structure

```
agenteval/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI entry point
│       ├── models.py        # Core data structures
│       ├── worker.py        # RQ worker process
│       ├── api/
│       │   └── routes.py    # HTTP endpoints
│       ├── core/
│       │   ├── config.py    # Settings
│       │   ├── store.py     # In-memory store
│       │   └── queue.py     # Redis queue
│       ├── db/
│       │   ├── database.py  # SQLAlchemy setup
│       │   ├── orm.py       # Table definitions
│       │   └── repository.py# DB read/write
│       └── runner/
│           ├── engine.py    # Test execution engine
│           └── generator.py # LLM scenario generation
├── mock_agent/
│   └── server.py            # Fake agent for local testing
├── scripts/
│   └── e2e_test.py          # End-to-end test script
├── tests/                   # Unit tests (21 passing)
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Running Tests

```bash
cd backend
pytest ../tests/ -v
```

21 tests, all passing, no external dependencies needed.

---

## Roadmap

- [x] HTTP endpoint agent connection
- [x] Automatic test scenario generation via LLM
- [x] Full execution trace recording
- [x] Pass/fail reporting with exact failure points
- [x] Loop detection
- [x] Postgres persistence
- [x] Redis job queue
- [x] GitHub Actions CI
- [ ] Results dashboard (Next.js) — in progress
- [ ] GitHub Actions integration for agent repos
- [ ] Voice agent support
- [ ] Cloud-hosted version

---

## Contributing

MIT licensed. PRs welcome.

```bash
git clone https://github.com/Fizza-Mukhtar/agentEval
cd agenteval
pip install -r requirements-dev.txt
cd backend && pytest ../tests/ -v
```

---

## License

MIT © 2026 AgentEval Contributors

---

<p align="center">
  <strong>AgentEval</strong> 
  <br/>
  <em>Built by developers who got tired of agents silently failing in production.</em>
</p>
