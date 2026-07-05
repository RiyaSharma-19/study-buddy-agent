# StudyDx – Multi-Agent Adaptive Learning Assistant

## Problem

Most existing study tools can generate flashcards, summarize notes, or create quizzes. However, they usually stop at telling learners **what** they got wrong. They rarely diagnose **why** a learner made a mistake, even though forgetting a concept, misunderstanding it, and making a careless error require different learning strategies.

StudyDx addresses this gap by using multiple AI agents that collaborate to generate study material, diagnose learning mistakes, and recommend personalized review schedules.

---

## Solution

StudyDx is a multi-agent learning assistant built using Google's Agent Development Kit (ADK). It accepts either a study topic or user-provided notes, generates flashcards, evaluates learner responses, classifies the type of mistake, and recommends when the learner should review the concept again.

Instead of treating every incorrect answer the same, StudyDx adapts feedback and review intervals based on the learner's mistake.

---

## Features

- Generate flashcards from study topics or notes
- Multi-agent workflow built using Google ADK
- Human-in-the-loop learning
- Diagnose learner mistakes into:
  - Forgot
  - Misunderstood
  - Careless Error
- Personalized review scheduling
- Input validation and security checks
- Structured outputs using Pydantic models

---

## Architecture

```
                    User
                      │
                      ▼
             Validation Agent
                      │
                      ▼
              Content Agent
                      │
                      ▼
          Flashcard Generation
                      │
                      ▼
            Human Answer Input
                      │
                      ▼
               Tutor Agent
        (Mistake Classification)
                      │
                      ▼
              Planner Agent
      (Review Recommendation)
```

### Validation Agent

Validates and sanitizes user input before it enters the workflow.

### Content Agent

Generates flashcards from user notes or a study topic.

### Tutor Agent

Evaluates the learner's response, classifies the mistake as **Forgot**, **Misunderstood**, or **Careless Error**, and provides personalized feedback.

### Planner Agent

Determines the recommended review interval based on the Tutor Agent's diagnosis.

---

## Technology Stack

- Python
- Google Agent Development Kit (ADK)
- Google Gemini
- Streamlit
- Pydantic
- SQLite
- Wikipedia content retrieval

---

## Google ADK Concepts Demonstrated

- Multi-Agent Workflow
- Human-in-the-Loop Interaction
- Structured Outputs
- Workflow Orchestration
- State Management
- Input Validation

---

## Project Structure

```text
study_buddy_agent/
├── app/
├── ui/
├── requirements.txt
├── README.md
└── .env.example
```

---

## Setup

```bash
git clone https://github.com/RiyaSharma-19/study-buddy-agent.git

cd study-buddy-agent
```

Create a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
GEMINI_API_KEY=YOUR_API_KEY
```

Run the backend and then launch the Streamlit frontend.

---

## Demo

*A demo video link will be added after submission.*

---

## Future Improvements

- Adaptive spaced repetition using learning history
- Multiple flashcards per study session
- Progress analytics dashboard
- PDF and document support
- Voice-based interaction

---

## Author

**Riya Sharma**

Developed as part of the **Google AI Agents Intensive Vibe Coding Capstone Project**.
