# StudyDx

## Problem
Existing study tools (flashcard generators, note summarizers, video
summarizers) generate content well, but stop at telling a student WHAT
they got wrong. They don't diagnose WHY -- forgot the concept entirely,
misunderstood it, or just made a careless slip -- even though each of
those needs a completely different next step.

## Solution
StudyDx is a multi-agent study assistant that classifies the *type* of
mistake a student makes and adapts both its explanation and its review
scheduling based on that diagnosis, instead of treating every wrong
answer the same way.

## Architecture
[Diagram goes here -- a simple boxes-and-arrows sketch is fine]

- **Content Agent** (`content_agent.py`) -- generates flashcards from
  pasted notes, OR fetches real reference content via an MCP server first
  if the user only gives a topic name (no notes)
- **Tutor Agent** (`tutor_agent.py`) -- the core differentiator: classifies
  a wrong answer as "forgot" / "misunderstood" / "careless", and gives a
  tailored explanation for that specific category
- **Planner Agent** (`planner_agent.py`) -- decides how many days until a
  card resurfaces for review, based on the Tutor Agent's classification
- **Security layer** (`security.py`) -- validates and sanitizes all user
  input before it reaches any agent: blocks prompt-injection attempts,
  oversized input, and ensures any local data writes stay inside the
  project's own data directory

## Tech Stack
- Google ADK 2.0 (graph-based workflow)
- Gemini API
- MCP Server (topic content fetch)
- Antigravity (agentic IDE used to build this project)
- Python 3.11+

## Course Concepts Demonstrated
1. Multi-agent system (ADK) -- see `agent.py` for the workflow graph
2. MCP Server -- see `fetch_topic_content()` in `content_agent.py`
3. Security features -- see `security.py`
4. Antigravity -- used throughout development (shown in demo video)

## Setup Instructions
1. Clone the repo:
   `git clone https://github.com/RiyaSharma-19/studydx-agent.git`
2. Create a `.env` file (copy `.env.example`) and add your real Gemini API
   key -- get one free at Google AI Studio
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `agents-cli playground` (opens the local ADK playground to test
   the agent interactively)

## Demo Video
[YouTube link once recorded]

## Author
Riya Sharma -- built as a real study tool for my own engineering
coursework, then generalized so it works on any subject's notes.
