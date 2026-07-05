"""
Run this from study_buddy_agent folder to inspect what's actually in sessions.db
"""
import sqlite3
import json
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "sessions.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # Get all events ordered by timestamp
    cursor.execute("SELECT id, invocation_id, event_data FROM events ORDER BY timestamp DESC LIMIT 20")
    events = cursor.fetchall()
    print(f"\nTotal recent events: {len(events)}")
    for i, (eid, inv_id, event_data) in enumerate(events):
        data = json.loads(event_data) if event_data else {}
        content = data.get("content", {})
        parts = content.get("parts", []) if content else []
        has_fc = any("functionCall" in str(p) for p in parts)
        long_running = data.get("long_running_tool_ids") or data.get("longRunningToolIds")
        print(f"  [{i}] id={eid[:8]}... inv={inv_id[:8] if inv_id else 'None'}... has_fc={has_fc} long_running={long_running} author={data.get('author','?')}")
        if has_fc:
            print(f"       FUNCTION CALL FOUND: {parts}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
