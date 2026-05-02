# AgentEval 🧪

**The missing test framework for AI agents.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> *Because guessing whether your agent works is not good enough.*

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

AgentEval is an **open-source agent testing platform** that tests the full behavioral reliability of your agent — not just its output quality.

| What existing tools test | What AgentEval tests |
|---|---|
| ✅ Was the LLM response accurate? | ✅ Was the **right tool** called? |
| ✅ Was the output well-formatted? | ✅ Were steps executed in the **correct sequence**? |
| ❌ Did the agent loop? | ✅ Did the agent **recover from failures**? |
| ❌ Did it call the wrong tool? | ✅ Did it complete within the **expected step count**? |
| ❌ What broke after re-deployment? | ✅ What **regressed** after your last deploy? |

---

## Quick Start

```bash
pip install agenteval
```

```python
from agenteval import AgentEval

eval = AgentEval(
    agent_endpoint="http://localhost:8000/run",
    task="Book a flight from Karachi to Dubai for next Friday",
    expected_tools=["search_flights", "check_availability", "book_ticket"],
    max_steps=10
)

results = eval.run()
results.summary()
```

```
✅ Passed: 7/10 scenarios
❌ Failed: 3/10 scenarios

Failure breakdown:
  - Scenario 4: Called 'search_hotels' before 'check_availability' (wrong order)
  - Scenario 7: Loop detected at step 6 — agent called 'search_flights' 3x with same params
  - Scenario 9: Task abandoned at step 4 — no recovery after API timeout
```

---

## Core Features

### 🧠 Automatic Test Scenario Generation
Describe your agent — AgentEval uses an LLM to generate 10 test scenarios automatically: 3 happy paths, 4 failure cases, 3 edge cases. No manual test writing.

### 🔍 Full Execution Tracing
Every test run captures a complete trace:
- Which tool was called at each step
- What parameters were passed
- What was returned
- Where loops occurred
- Whether the agent recovered or gave up

### 📊 Pass/Fail Reporting
Clear, structured results — not just logs:
- Expected vs actual tool call sequence
- Task completion rate
- Failure point identification
- Step count analysis

### 🔄 GitHub Actions Integration
```yaml
- name: Run AgentEval
  uses: agenteval/action@v1
  with:
    agent_endpoint: ${{ secrets.AGENT_ENDPOINT }}
    config: agenteval.yml
```

Run regression tests automatically on every deployment.

---

## How It Works

```
Developer defines agent → AgentEval generates test scenarios (via LLM)
       ↓
Each scenario sends a real task to your agent's HTTP endpoint
       ↓
AgentEval records the full execution trace (tools, params, steps, loops)
       ↓
Pass/Fail report + dashboard visualization
```

---

## Architecture

```
agenteval/
├── backend/          # FastAPI — test runner + execution engine
│   ├── runner/       # Sends tasks, records traces
│   ├── evaluator/    # Pass/fail logic, loop detection
│   └── generator/    # LLM-based scenario generation
├── sandbox/          # Docker — isolated agent execution
├── dashboard/        # Next.js — results UI
└── integrations/     # GitHub Actions, CI/CD
```

**Tech stack:** Python + FastAPI · Docker · PostgreSQL · Redis · Next.js · Claude API

---

## Roadmap

- [x] HTTP endpoint agent connection
- [x] Automatic test scenario generation
- [x] Execution trace recording
- [x] Pass/fail reporting + dashboard
- [x] GitHub Actions integration
- [ ] Voice agent support
- [ ] Team collaboration features
- [ ] Cloud-hosted version (AgentEval Cloud)
- [ ] Support for browser-use agents
- [ ] Playwright-based web action tracing

---

## Contributing

AgentEval is MIT licensed and community-driven.

```bash
git clone https://github.com/yourusername/agenteval
cd agenteval
pip install -e ".[dev]"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Why Open Source?

Agent testing should be a community standard — not a paid feature.

We're following the DeepEval/Confident AI playbook: give developers real value first, build the cloud platform later. The core will always be free.

---

## Star History

If AgentEval saves you even one production incident, **please star this repo** ⭐  
It helps other developers discover it.

---

## License

MIT © 2026 AgentEval Contributors

---

<p align="center">
  <strong>AgentEval</strong> · <a href="https://twitter.com/agenteval">Twitter</a> · <a href="https://discord.gg/agenteval">Discord</a>
  <br/>
  <em>Built by developers who got tired of agents silently failing in production.</em>
</p>
