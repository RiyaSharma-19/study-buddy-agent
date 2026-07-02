# Study Buddy Agent — Progress Log
*Project concept name: StudyDx. The technical agent name is `study_buddy_agent`
because ADK requires valid Python identifiers — hyphens and stylized names like
"StudyDx" aren't valid as folder names or App(name=) values. The branding name
was kept for the README and writeup; the codebase uses `study_buddy_agent`
throughout for compatibility.*

---
## June 22 — Project Setup & Planning

**What I built/changed:**
- Decided on project name "StudyDx" — wanted something that signals
  diagnosis, not just flashcards. Most study tools already exist, so
  the pitch had to be about WHY a student gets something wrong, not
  just generating content
- Settled on 3 agents: Content Agent (flashcards), Tutor Agent
  (mistake diagnosis), Planner Agent (review scheduling)
- Added a 4th decision layer: if user only gives a topic name (no notes),
  fetch real content from Wikipedia first before generating flashcards —
  this became the MCP integration
- Started scaffolding with Antigravity but quota ran out mid-way

**What broke / had to debug:**
- Antigravity quota exhausted during scaffold — had to pause and manually
  set up project structure files while waiting for quota to refresh
- Wasn't sure at this point whether the ADK workflow graph syntax I was
  using was even correct — couldn't test it yet

**Why I made this decision:**
- 3 mistake categories (forgot/misunderstood/careless) instead of just
  right/wrong — because each one needs a genuinely different response.
  Telling someone to "review again" when they misunderstood something is
  useless; they need the misconception corrected directly
- Kept the notes-vs-topic routing as plain code, not an LLM call —
  it's a simple if/else check, burning API quota on it made no sense

**Anything that surprised me:**
- The security layer needs to actually be called on every input to mean
  anything — having a security.py file that nothing calls is just decoration

---

## June 25-26 — Environment & Files

**What I built/changed:**
- Set up .env with GOOGLE_API_KEY, confirmed .gitignore excludes it
- Created README skeleton
- Copied scaffold files into project while waiting for Antigravity quota

**What broke / had to debug:**
- pytest gave "command not found" — virtual environment wasn't activated,
  fixed by using .venv\Scripts\python.exe -m pytest directly
- Had two competing agent.py files (one from my manual scaffold, one from
  Antigravity's actual build) — spent time debugging errors caused by
  the wrong file being loaded silently. Took a while to figure out what
  was actually happening

**Why I made this decision:**
- Used Wikipedia's free REST API for topic content fetching — real external
  data, no cost, no API key needed for basic summaries

**Anything that surprised me:**
- I didn't realise ADK's agent_loader has two separate discovery mechanisms.
  The FastAPI server uses an explicit App object, but the /run_sse endpoint
  uses a filesystem path lookup for agent.py — these need to be consistent
  or you get confusing 500 errors that look like code bugs

---

## June 29 — Server Debugging

**What I built/changed:**
- Fixed fast_api_app.py — removed Google Cloud authentication dependency
  that the Antigravity scaffold included by default
- Confirmed the core workflow logic runs correctly when called directly

**What broke / had to debug:**
- Server crashed immediately on startup: google.auth.default() failed
  because it expected GCP credentials I don't have. The scaffold was
  written for cloud deployment, not local use
- App name "study-buddy-agent" (with hyphens) got rejected by ADK as an
  invalid Python identifier — renamed everything to study_buddy_agent
  with underscores
- Even after fixing the name, session lookups were failing because
  App(name=) in agent.py didn't match the folder-derived name the runner
  was using. These were the same problem in different layers

**Why I made this decision:**
- Stripped all GCP dependencies from fast_api_app.py — the project is
  local/demo-only, there's no reason to require Cloud credentials just
  to run it

**Anything that surprised me:**
- Most of the server errors during this session weren't agent logic bugs —
  they were infrastructure mismatches (naming conventions, path resolution,
  GCP vs local setup). The actual workflow code was correct the whole time

---

## July 2 — Full End-to-End Working + Tests Passing

**What I built/changed:**
- All 5 pytest tests passing
- Fixed test_server_e2e.py: updated hardcoded "app" name references,
  fixed assertion to accept functionCall events (answer_gate human-in-the-
  loop interrupt) as valid responses — not just text
- Confirmed full workflow manually via API:
  Input: "Photosynthesis" (topic only, no notes)
  → validate_input passed
  → routed to topic_only path
  → Wikipedia fetch returned real photosynthesis summary
  → content_agent generated 6 real flashcards from that content
  → answer_gate paused and asked: "What is photosynthesis?"
  → waiting for user answer before Tutor Agent classifies mistake type

**What broke / had to debug:**
- find-and-replace in VS Code replaced "app" inside an f-string URL,
  breaking the syntax — had to manually fix the closing quote

**Why I made this decision:**
- Kept answer_gate as a genuine human-in-the-loop pause rather than
  faking it in tests — the whole point of the project is that the agent
  waits for your real answer before diagnosing anything

**Anything that surprised me:**
- Once the right agent.py was actually being loaded, everything worked
  first try. The debugging time was almost entirely infrastructure, not
  agent logic. That's both relieving and slightly annoying in retrospect