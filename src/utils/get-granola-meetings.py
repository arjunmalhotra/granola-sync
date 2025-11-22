#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Load the Granola cache
cache_path = "/Users/arjunmalhotra/Library/Application Support/Granola/cache-v3.json"
with open(cache_path, 'r') as f:
    data = json.load(f)

# Parse the nested JSON
cache = json.loads(data['cache'])

# Extract meetings with notes
meetings = []
if 'state' in cache and 'notes' in cache['state']:
    for note_id, note in cache['state']['notes'].items():
        if isinstance(note, dict):
            meetings.append({
                'id': note_id,
                'title': note.get('title', 'Untitled'),
                'date': note.get('date', 'Unknown'),
                'content': note.get('content', ''),
                'summary': note.get('summary', '')
            })

# Sort by date (most recent first)
meetings.sort(key=lambda x: x.get('date', ''), reverse=True)

# Print the last 5 meetings
print(f"Found {len(meetings)} meetings with notes\n")
print("="*80)

for i, meeting in enumerate(meetings[:5], 1):
    print(f"\n📅 Meeting {i}: {meeting['title']}")
    print(f"Date: {meeting['date']}")
    print(f"\n--- Summary ---")
    print(meeting['summary'] if meeting['summary'] else "No summary available")
    print(f"\n--- Notes ---")
    content = meeting['content'][:1000] if meeting['content'] else "No notes"
    print(content)
    if len(meeting['content']) > 1000:
        print(f"\n... (truncated, {len(meeting['content'])} total characters)")
    print("\n" + "="*80)
