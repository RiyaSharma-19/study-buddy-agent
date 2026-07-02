# StudyDx — Progress Log

## June 26 — Session log

**What I built/changed:**
- Got the ADK + MCP + Antigravity scaffold for the project's structure
  (Content Agent, Tutor Agent, Planner Agent, security validation)

**What broke / had to debug:**
- Antigravity quota ran out partway through scaffolding (Prompt 2), so the
  multi-agent file structure was written manually instead, to review and
  hand to Antigravity once quota resumes

**Why I made this decision:**
- Locked the project name as "StudyDx" -- short, signals the core idea
  (diagnosis, not just flashcards) without needing explanation
- Decided mistake classification needs exactly 3 categories (forgot /
  misunderstood / careless) because each genuinely needs a different
  response -- more categories would blur the distinction, fewer would
  lose the point of diagnosing at all
- Kept the input-type router (notes vs. topic-only) as plain code, not an
  LLM call, since it's a simple, unambiguous check -- no reason to spend
  API quota on it

**Anything that surprised me:**
- Realized the security layer needed to be a real, callable function that
  every input passes through -- not just a comment/intention -- for it to
  count as an actual demonstrated concept, not a decorative one


<!-- Copy the block below for each new session -->

## [Date] — Session log

**What I built/changed:**
-

**What broke / had to debug:**
-

**Why I made this decision:**
-

**Anything that surprised me:**
-
