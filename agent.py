"""
Re-export point for ADK's single-agent auto-discovery, which expects a
plain agent.py at the project root. The real logic lives in app/agent.py
-- this file just points to it, so there's one source of truth.
"""
from app.agent import root_agent, app