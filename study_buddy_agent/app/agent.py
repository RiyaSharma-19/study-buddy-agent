# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import urllib.request
import urllib.parse
import json
from pydantic import BaseModel, Field
from typing import Any, Literal
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()

from google.adk.agents import Agent, Context
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.workflow import Workflow, START, node
from google.adk.events.request_input import RequestInput
from google.genai import types

# Define shared schemas
class Flashcard(BaseModel):
    question: str = Field(description="The question of the flashcard.")
    answer: str = Field(description="The correct answer to the question.")

class ContentAgentOutput(BaseModel):
    flashcards: list[Flashcard] = Field(description="List of flashcards generated from the notes.")

class TutorOutput(BaseModel):
    classification: Literal["forgot", "misunderstood", "careless error"] = Field(
        description="Classification of the user's mistake."
    )
    explanation: str = Field(
        description="Tailored explanation for the user based on the classification."
    )

class PlannerOutput(BaseModel):
    classification: Literal["forgot", "misunderstood", "careless error"] = Field(
        description="The mistake classification received from the Tutor Agent."
    )
    review_delay_days: int = Field(
        description="Number of days before the card should be reviewed again."
    )
    explanation: str = Field(
        description="Explanation of the planning decision."
    )

# Security / Validation logic
MAX_INPUT_CHARS = 4000
SUSPICIOUS_PATTERNS = [
    r"ignore (all|previous|your) instructions",
    r"system prompt",
    r"you are now",
    r"disregard (the )?(above|previous)",
    r"act as (if|though)",
]

class InputValidationError(Exception):
    pass

def validate_user_input(text: str) -> str:
    if text is None:
        raise InputValidationError("Input cannot be empty.")
    text = text.strip()
    if len(text) == 0:
        raise InputValidationError("Input cannot be empty.")
    if len(text) > MAX_INPUT_CHARS:
        raise InputValidationError(
            f"Input too long ({len(text)} chars). Limit is {MAX_INPUT_CHARS}."
        )
    lowered = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, lowered):
            raise InputValidationError(
                "Input contains a phrase commonly associated with prompt "
                "injection attempts and was blocked."
            )
    return text

# Wikipedia Reference content fetching logic
def fetch_wikipedia_summary(topic: str) -> str:
    try:
        encoded_topic = urllib.parse.quote(topic)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "StudyDxAgent/1.0 (studydx; riya-sharma)"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("extract", f"No Wikipedia extract found for '{topic}'.")
    except Exception as e:
        return f"Could not fetch reference content for '{topic}' from Wikipedia. Error: {str(e)}"

# Common model configuration
shared_model = Gemini(
    model="gemini-2.5-flash",
    retry_options=types.HttpRetryOptions(attempts=3),
)

# Helper to extract text from various input formats
def extract_text_from_input(node_input: Any) -> str:
    if isinstance(node_input, str):
        return node_input
    if isinstance(node_input, dict):
        return node_input.get("notes") or node_input.get("topic") or ""
    if hasattr(node_input, "notes"):
        return getattr(node_input, "notes") or ""
    if hasattr(node_input, "topic"):
        return getattr(node_input, "topic") or ""
    if hasattr(node_input, "parts") and node_input.parts:
        parts_text = []
        for part in node_input.parts:
            if hasattr(part, "text") and part.text:
                parts_text.append(part.text)
        return "".join(parts_text)
    return str(node_input)

# Nodes for workflow

# 1) Validation Node (Security)
@node(name="validate_input")
def validate_input_node(ctx: Context, node_input: types.Content):
    raw_text = extract_text_from_input(node_input)
    try:
        cleaned = validate_user_input(raw_text)
    except InputValidationError as e:
        # Stop workflow by setting route to blocked
        ctx.route = "blocked"
        ctx.state["error"] = str(e)
        return {"error": str(e)}

    ctx.route = "ok"
    # Return formatted dict based on length
    if len(cleaned) > 30:
        return {"notes": cleaned}
    else:
        return {"topic": cleaned}

# 2) Router Node (Deterministic routing based on input notes length)
@node(name="decide_input_type")
def decide_input_type(ctx: Context, node_input: dict):
    notes = (node_input.get("notes") or "").strip()
    topic = (node_input.get("topic") or "").strip()

    if not notes and topic:
        ctx.route = "topic_only"
        return {"topic": topic}

    # If notes contains actual text longer than 30 chars, route to has_notes
    if len(notes) > 30:
        ctx.route = "has_notes"
        return {"notes": notes}
    else:
        topic_name = topic or notes
        ctx.route = "topic_only"
        return {"topic": topic_name}

# 3) Fetch Reference Content Node
@node(name="fetch_topic_content")
def fetch_topic_content(ctx: Context, node_input: dict):
    topic = node_input.get("topic", "")
    fetched_text = fetch_wikipedia_summary(topic)
    return {"notes": fetched_text}

# 4) Content Agent
content_agent = Agent(
    name="content_agent",
    model=shared_model,
    instruction=(
        "You are the Content Agent. Your task is to take raw study notes as text and "
        "generate flashcards (question/answer pairs) based on them. Focus on key definitions, "
        "concepts, and details. Output the flashcards strictly matching the output schema."
    ),
    output_schema=ContentAgentOutput,
)

# Human-in-the-Loop Node
@node(name="answer_gate", rerun_on_resume=True)
def answer_gate(ctx: Context, node_input: Any):
    interrupt_id = "user_answer"

    # Resolve flashcards from input
    if hasattr(node_input, "flashcards"):
        flashcards = node_input.flashcards
    elif isinstance(node_input, dict):
        flashcards = node_input.get("flashcards", [])
    else:
        flashcards = []

    # If resumed, flashcards come from state (saved during first execution)
    if interrupt_id in ctx.resume_inputs:
        user_answer = ctx.resume_inputs[interrupt_id]
        if isinstance(user_answer, dict):
            user_answer = user_answer.get("answer", "")
        
        # Load flashcard from state
        flashcard = ctx.state.get("current_flashcard", {})
        question = flashcard.get("question", "Unknown question") if isinstance(flashcard, dict) else str(flashcard)
        answer = flashcard.get("answer", "Unknown answer") if isinstance(flashcard, dict) else ""
        
        # Return explicit JSON string so Tutor Agent actually receives it
        import json as _json
        tutor_payload = _json.dumps({
            "flashcard": {"question": question, "answer": answer},
            "user_answer": user_answer
        })
        ctx.state["tutor_input"] = tutor_payload
        return {"tutor_input": tutor_payload}

    # First execution: save flashcard to state and request input
    if not flashcards:
        raise ValueError("No flashcards generated by the Content Agent.")

    flashcard = flashcards[0]
    if hasattr(flashcard, "question"):
        question = flashcard.question
        correct_answer = flashcard.answer
    elif isinstance(flashcard, dict):
        question = flashcard.get("question", "No question found")
        correct_answer = flashcard.get("answer", "")
    else:
        question = str(flashcard)
        correct_answer = ""

    # Save to state so it survives the HTTP boundary
    ctx.state["current_flashcard"] = {"question": question, "answer": correct_answer}

    yield RequestInput(
        interrupt_id=interrupt_id,
        message=f"Flashcard Question: {question}\n\nPlease submit your answer:",
        response_schema={"type": "object", "properties": {"answer": {"type": "string"}}}
    )

# 5) Tutor Agent
tutor_agent = Agent(
    name="tutor_agent",
    model=shared_model,
    instruction=(
        "You are the Tutor Agent. Evaluate this study session data:\n\n"
        "{tutor_input}\n\n"
        "The JSON above contains the flashcard (question and correct answer) and the user_answer. "
        "Parse it and evaluate whether the user_answer is correct given the flashcard's correct answer. "
        "Classify the mistake as exactly one of: 'forgot', 'misunderstood', or 'careless error'. "
        "Provide a tailored explanation. Strictly adhere to the output schema."
        "- 'misunderstood': ONLY if the user states something factually wrong or demonstrates a clear misconception. An incomplete answer is NOT misunderstood.\n"
        "- 'careless error': if the user's answer is correct OR incomplete but not wrong. If the core concept is right but details are missing, this is careless error, not misunderstood.\n"
    ),
    output_schema=TutorOutput,
)

# 6) Planner Agent
planner_agent = Agent(
    name="planner_agent",
    model=shared_model,
    instruction=(
        "You are the Planner Agent. You will receive the Tutor Agent's classification of the user's mistake. "
        "Decide when this flashcard should be reviewed again based on the classification:\n"
        "- For 'forgot': review_delay_days must be 1 day (reinforce memory quickly).\n"
        "- For 'misunderstood': review_delay_days must be 3 days (reinforce concept after correction).\n"
        "- For 'careless error': review_delay_days must be 7 days (longer gap since user understood concept).\n"
        "Format your output strictly according to the output schema."
    ),
    output_schema=PlannerOutput,
)

# Define the workflow graph
root_agent = Workflow(
    name="study_buddy_workflow",
    edges=[
        (START, validate_input_node),
        (validate_input_node, {
            "ok": decide_input_type,
        }),
        (decide_input_type, {
            "has_notes": content_agent,
            "topic_only": fetch_topic_content,
        }),
        (fetch_topic_content, content_agent),
        (content_agent, answer_gate),
        (answer_gate, tutor_agent),
        (tutor_agent, planner_agent),
    ]
)

app = App(
    root_agent=root_agent,
    name="study_buddy_agent",
)
