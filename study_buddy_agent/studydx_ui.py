"""
studydx_ui.py

StudyDx — Streamlit frontend
Calls the local FastAPI/ADK backend (uvicorn on port 8000).
Run this AFTER starting the backend:
    cd study_buddy_agent
    .venv\Scripts\python.exe -m uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000

Then in a second terminal:
    cd study_buddy_agent
    .venv\Scripts\python.exe -m streamlit run studydx_ui.py
"""

import json
import uuid
import requests
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000"
APP_NAME = "study_buddy_agent"
USER_ID  = "studydx_user"

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="StudyDx", page_icon="🧠", layout="centered")

st.markdown("""
    <h1 style='text-align:center; color:#4A90D9;'>🧠 StudyDx</h1>
    <p style='text-align:center; color:gray;'>
        Diagnoses <em>why</em> you got something wrong — not just that you did.
    </p>
    <hr>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id"       not in st.session_state: st.session_state.session_id       = None
if "flashcard"        not in st.session_state: st.session_state.flashcard         = None
if "interrupt_id"     not in st.session_state: st.session_state.interrupt_id      = None
if "invocation_id"    not in st.session_state: st.session_state.invocation_id     = None
if "result"           not in st.session_state: st.session_state.result            = None
if "stage"            not in st.session_state: st.session_state.stage             = "input"
# stage: input → answering → result

# ── Helpers ───────────────────────────────────────────────────────────────────
def create_session() -> str:
    r = requests.post(
        f"{BASE_URL}/apps/{APP_NAME}/users/{USER_ID}/sessions",
        json={"state": {}},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["id"]


def send_message(session_id: str, text: str) -> list[dict]:
    """Send a message and collect all SSE events."""
    payload = {
        "app_name":   APP_NAME,
        "user_id":    USER_ID,
        "session_id": session_id,
        "new_message": {
            "role":  "user",
            "parts": [{"text": text}],
        },
        "streaming": True,
    }
    events = []
    with requests.post(f"{BASE_URL}/run_sse", json=payload,
                       stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    try:
                        events.append(json.loads(line_str[6:]))
                    except json.JSONDecodeError:
                        pass
    return events


def resume_session(session_id: str, invocation_id: str,
                   interrupt_id: str, answer: str) -> list[dict]:
    """Resume a paused workflow with the user's answer."""
    payload = {
        "app_name":   APP_NAME,
        "user_id":    USER_ID,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{
                "functionResponse": {
                    "id": interrupt_id,
                    "name": "adk_request_input",
                    "response": {"answer": answer}
                }
            }]
        },
        "streaming": True,
    }
    events = []
    with requests.post(f"{BASE_URL}/run_sse", json=payload,
                       stream=True, timeout=60) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    try:
                        events.append(json.loads(line_str[6:]))
                    except json.JSONDecodeError:
                        pass
    return events


def extract_flashcard(events: list[dict]) -> tuple[dict | None, str | None, str | None]:
    """
    Pull the flashcard question, interrupt_id, and invocation_id
    from the answer_gate event.
    """
    for e in events:
        content = e.get("content", {})
        if not content:
            continue
        for part in content.get("parts", []):
            fc = part.get("functionCall", {})
            if fc.get("name") == "adk_request_input":
                args         = fc.get("args", {})
                interrupt_id = args.get("interruptId")
                message      = args.get("message", "")
                inv_id       = e.get("invocationId")
                # Parse question from message: "Flashcard Question: X\n\nPlease submit..."
                question = message.split("\n")[0].replace("Flashcard Question: ", "").strip()
                return {"question": question}, interrupt_id, inv_id
    return None, None, None


def extract_tutor_result(events: list[dict]) -> dict | None:
    for e in reversed(events):
        if e.get("author") != "tutor_agent":
            continue
        if e.get("partial"):
            continue
        content = e.get("content", {})
        for part in (content.get("parts", []) if content else []):
            text = part.get("text", "")
            if not text:
                continue
            try:
                text = text.strip().strip("```json").strip("```").strip()
                data = json.loads(text)
                if "classification" in data:
                    return data
            except Exception:
                pass
    return None


def extract_planner_result(events: list[dict]) -> dict | None:
    for e in reversed(events):
        if e.get("author") != "planner_agent":
            continue
        if e.get("partial"):
            continue
        content = e.get("content", {})
        for part in (content.get("parts", []) if content else []):
            text = part.get("text", "")
            if not text:
                continue
            try:
                text = text.strip().strip("```json").strip("```").strip()
                data = json.loads(text)
                if "review_delay_days" in data:
                    return data
            except Exception:
                pass
    return None


# ── Badge colours per mistake type ───────────────────────────────────────────
BADGE = {
    "forgot":        ("🔴", "#FF4B4B", "You didn't recall this concept at all."),
    "misunderstood": ("🟠", "#FF8C00", "You recalled something, but got the concept wrong."),
    "careless error":("🟡", "#FFD700", "You understood it — just a small slip."),
    "careless":      ("🟡", "#FFD700", "You understood it — just a small slip."),
}

# ── STAGE 1: Input ────────────────────────────────────────────────────────────
if st.session_state.stage == "input":
    st.subheader("📋 Step 1 — Paste your notes or enter a topic")

    input_type = st.radio("Input type", ["Topic name", "My own notes"],
                          horizontal=True)

    if input_type == "Topic name":
        user_input = st.text_input("Topic (e.g. Photosynthesis, Laplace Transform)",
                                   placeholder="Type a topic...")
    else:
        user_input = st.text_area("Paste your study notes here",
                                  height=200,
                                  placeholder="Paste your notes...")

    if st.button("🚀 Generate Flashcard", use_container_width=True):
        if not user_input.strip():
            st.warning("Please enter a topic or paste your notes first.")
        else:
            with st.spinner("Fetching content and generating flashcard..."):
                try:
                    sid = create_session()
                    st.session_state.session_id = sid
                    events = send_message(sid, user_input.strip())
                    fc, interrupt_id, inv_id = extract_flashcard(events)
                    if fc:
                        st.session_state.flashcard     = fc
                        st.session_state.interrupt_id  = interrupt_id
                        st.session_state.invocation_id = inv_id
                        st.session_state.stage         = "answering"
                        st.rerun()
                    else:
                        st.error("Could not generate a flashcard. Check that your backend server is running.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the server is running on port 8000.")
                except Exception as ex:
                    st.error(f"Error: {ex}")

# ── STAGE 2: Answer the flashcard ─────────────────────────────────────────────
elif st.session_state.stage == "answering":
    st.subheader("🃏 Step 2 — Answer the flashcard")

    fc = st.session_state.flashcard
    st.markdown(f"""
    <div style='background:#1E3A5F; padding:20px; border-radius:10px; margin-bottom:20px;'>
        <h3 style='color:#4A90D9; margin:0;'>Question</h3>
        <p style='color:white; font-size:18px; margin:10px 0 0 0;'>{fc['question']}</p>
    </div>
    """, unsafe_allow_html=True)

    answer = st.text_input("Your answer", placeholder="Type your answer here...")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit Answer", use_container_width=True):
            if not answer.strip():
                st.warning("Please type an answer first.")
            else:
                with st.spinner("Diagnosing your answer..."):
                    try:
                        events = resume_session(
                            st.session_state.session_id,
                            st.session_state.invocation_id,
                            st.session_state.interrupt_id,
                            answer.strip(),
                        )
                        tutor  = extract_tutor_result(events)
                        planner = extract_planner_result(events)
                        st.session_state.result = {
                            "answer":  answer.strip(),
                            "tutor":   tutor,
                            "planner": planner,
                            "events":  events,
                        }
                        st.session_state.stage = "result"
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error: {ex}")
    with col2:
        if st.button("🔄 Start Over", use_container_width=True):
            for key in ["session_id", "flashcard", "interrupt_id",
                        "invocation_id", "result"]:
                st.session_state[key] = None
            st.session_state.stage = "input"
            st.rerun()

# ── STAGE 3: Result ───────────────────────────────────────────────────────────
elif st.session_state.stage == "result":
    st.subheader("🔍 Step 3 — Diagnosis")

    result  = st.session_state.result
    tutor   = result.get("tutor") or {}
    planner = result.get("planner") or {}

    classification = (
        tutor.get("classification")
        or tutor.get("mistake_type")
        or "unknown"
    ).lower()

    is_correct = tutor.get("is_correct", False)
    explanation = tutor.get("explanation", "")
    review_days = planner.get("review_delay_days")

    if is_correct:
        st.success("✅ Correct! Well done.")
        if review_days:
            st.info(f"📅 Next review in **{review_days} days** — you've got this one down.")
    else:
        emoji, color, subtitle = BADGE.get(
            classification, ("⚪", "#888", "Mistake classified.")
        )
        st.markdown(f"""
        <div style='background:{color}22; border-left:5px solid {color};
                    padding:15px; border-radius:8px; margin-bottom:15px;'>
            <h3 style='color:{color}; margin:0;'>{emoji} {classification.title()}</h3>
            <p style='color:gray; margin:4px 0 0 0; font-size:14px;'>{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

        if explanation:
            st.markdown("**What the Tutor Agent says:**")
            st.markdown(f"> {explanation}")

        if review_days:
            st.info(f"📅 Review this card again in **{review_days} day(s)**")

    st.divider()
    st.markdown("**Your answer:** " + result.get("answer", ""))
    st.markdown("**Flashcard question:** " + (st.session_state.flashcard or {}).get("question", ""))

    if st.button("🔄 Try Another Topic", use_container_width=True):
        for key in ["session_id", "flashcard", "interrupt_id",
                    "invocation_id", "result"]:
            st.session_state[key] = None
        st.session_state.stage = "input"
        st.rerun()
