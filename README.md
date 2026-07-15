# StudyDx — Multi-Agent Study Assistant

> Diagnoses *why* you got something wrong — not just that you did.

**Track:** Concierge Agents · Google AI Agents Intensive Vibe Coding Capstone 2026

**Note on naming:** The project is branded as *StudyDx*. The technical identifier throughout the codebase is `study_buddy_agent` — ADK requires valid Python identifiers for folder and App names, which rules out stylized names. Both names refer to the same project.

---

## The Problem

Most study tools stop at telling you what you got wrong. They don't distinguish between:

- **Forgot** — you had no recollection of the concept at all
- **Misunderstood** — you recalled something, but applied the wrong concept
- **Careless error** — you knew the answer but made a small slip

Each of these needs a different response. Restating the correct answer helps a student who forgot. It doesn't help a student who misunderstood — they need the specific misconception corrected. StudyDx makes that distinction and responds accordingly.

---

## Solution

A graph-based multi-agent workflow built with Google ADK 2.3.0. The system accepts either study notes or a topic name, generates flashcards, pauses for the learner's answer, classifies the mistake type, and schedules the next review based on that classification.

---

## Architecture

![StudyDx Architecture](studydx_architecture.svg)

### Workflow nodes

| Node | Type | Responsibility |
|------|------|---------------|
| `validate_input` | Code (deterministic) | Sanitizes input, blocks prompt injection, enforces size limits |
| `decide_input_type` | Code (deterministic) | Routes to notes path or topic-only path — no LLM call |
| `fetch_topic_content` | Code + MCP | Calls Wikipedia REST API to fetch real content when no notes are provided |
| `content_agent` | LLM (Gemini 2.5 Flash) | Generates flashcards from notes or fetched content |
| `answer_gate` | HITL node | Suspends workflow, persists session to SQLite, resumes on user answer |
| `tutor_agent` | LLM (Gemini 2.5 Flash) | Classifies mistake as forgot / misunderstood / careless error |
| `planner_agent` | LLM (Gemini 2.5 Flash) | Schedules next review: forgot→1d, misunderstood→3d, careless→7d |

### Why two deterministic nodes instead of LLM calls

The input routing and validation decisions are unambiguous — they don't need AI reasoning. Using LLMs for deterministic checks wastes quota and introduces inconsistency. This is explicit ADK best practice.

### Why SQLite for session persistence

The HITL pause requires workflow state to survive between two separate HTTP requests — the one that generates the flashcard and the one that submits the user's answer. In-memory sessions lose state between requests. `session_service_uri="sqlite:///./sessions.db"` in the FastAPI app configuration is what makes the resume work.

---

## Google ADK Concepts Demonstrated

1. **Multi-agent system (ADK)** — graph workflow with explicit routing edges between five nodes
2. **MCP Server** — Wikipedia REST API called as an external tool via `fetch_topic_content`
3. **Security features** — input validation runs on every request before any LLM call; blocks prompt injection patterns
4. **Human-in-the-loop** — `RequestInput` interrupt with SQLite-persisted session state
5. **Antigravity** — used to scaffold and develop the project (shown in demo video)

---

## Tech Stack

- Google ADK 2.3.0
- Gemini 2.5 Flash
- Streamlit (frontend)
- FastAPI (ADK's `get_fast_api_app`)
- SQLite (session persistence)
- Wikipedia REST API (MCP content fetch)
- Pydantic (structured agent outputs)
- pytest (5/5 integration + unit tests passing)

---

## Project Structure

```
study-buddy-agent/
├── study_buddy_agent/
│   ├── app/
│   │   ├── agent.py          # Full workflow graph + all agent definitions
│   │   ├── fast_api_app.py   # FastAPI server (ADK get_fast_api_app)
│   │   └── app_utils/
│   ├── study_buddy_agent/
│   │   └── agent.py          # Re-export for ADK's filesystem discovery
│   ├── tests/
│   │   ├── integration/      # test_agent.py + test_server_e2e.py
│   │   └── unit/
│   ├── studydx_ui.py         # Streamlit frontend
│   └── sessions.db           # SQLite session store (auto-created on first run)
├── studydx_architecture.svg
├── progress-log.md
└── README.md
```

---

## Setup

**Requirements:** Python 3.11+, [`uv`](https://docs.astral.sh/uv/) package manager, Google AI Studio API key (free tier).

```bash
git clone https://github.com/RiyaSharma-19/study-buddy-agent.git
cd study-buddy-agent/study_buddy_agent
```

Create `app/.env`:
```
GOOGLE_API_KEY=your_key_here
```

Install dependencies:
```bash
uv pip install google-adk streamlit requests
```

**Terminal 1 — start backend:**
```bash
# Windows
.venv\Scripts\python.exe -m uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000

# Mac/Linux
.venv/bin/python -m uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000
```

**Terminal 2 — start Streamlit UI:**
```bash
# Windows
.venv\Scripts\python.exe -m streamlit run studydx_ui.py

# Mac/Linux
.venv/bin/python -m streamlit run studydx_ui.py
```

Open `http://localhost:8501`.

---

## Running Tests

```bash
# Windows
.venv\Scripts\python.exe -m pytest

# Mac/Linux
.venv/bin/python -m pytest
```

Expected: 5 passed.

---

## Demo Video

[YouTube link]

## GitHub

https://github.com/RiyaSharma-19/study-buddy-agent

---

## Limitations

- Mistake classification is probabilistic — edge cases (partially correct answers) occasionally get misclassified
- Review scheduling uses fixed delays, not a full spaced-repetition algorithm (SM-2/FSRS)
- Runs locally — no public deployment

---

## Future Improvements

- Adaptive spaced repetition using per-card learning history
- Multiple flashcards per session with progress tracking
- PDF and document upload support
- Hindi/English bilingual support (Gemini handles this natively)


---

## Author

**Riya Sharma** — 2nd year B.Tech CSE, Medicaps University, Indore
GitHub: [RiyaSharma-19](https://github.com/RiyaSharma-19)