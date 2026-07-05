"""
Run: .venv\Scripts\python.exe check_event.py sessions.db <event_id_prefix>
Shows the full event_data for a specific event
"""
import sqlite3
import json
import sys

db_path = sys.argv[1]
event_prefix = sys.argv[2] if len(sys.argv) > 2 else None

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

if event_prefix:
    cursor.execute("SELECT id, invocation_id, event_data FROM events WHERE id LIKE ?", (event_prefix + '%',))
else:
    cursor.execute("SELECT id, invocation_id, event_data FROM events ORDER BY timestamp DESC LIMIT 1")

rows = cursor.fetchall()
for eid, inv_id, event_data in rows:
    data = json.loads(event_data) if event_data else {}
    print(f"Event ID: {eid}")
    print(f"Invocation: {inv_id}")
    print(f"Author: {data.get('author')}")
    print(f"long_running_tool_ids: {data.get('long_running_tool_ids')}")
    content = data.get('content', {})
    parts = content.get('parts', []) if content else []
    for i, part in enumerate(parts):
        print(f"Part [{i}]: {json.dumps(part, indent=2)}")
conn.close()
