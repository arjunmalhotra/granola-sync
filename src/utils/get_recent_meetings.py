#!/usr/bin/env python3
"""
Quick script to get recent meetings from Granola cache
"""
import json
from datetime import datetime

# Load the cache file
cache_path = "/Users/arjunmalhotra/Library/Application Support/Granola/cache-v3.json"

with open(cache_path, 'r') as f:
    data = json.load(f)

# Double-JSON decoding (Granola's cache structure)
cache_data = json.loads(data['cache'])
state = cache_data.get('state', {})

documents_raw = state.get('documents', [])
# Convert documents to list if it's a dict
if isinstance(documents_raw, dict):
    documents = list(documents_raw.values())
else:
    documents = documents_raw

# Get the 5 most recent meetings
recent_meetings = documents[:5]

print("=" * 80)
print("RECENT MEETINGS FROM GRANOLA")
print("=" * 80)
print()

for i, meeting in enumerate(recent_meetings, 1):
    print(f"Meeting #{i}")
    print("-" * 80)
    print(f"Title: {meeting.get('title', 'Untitled')}")

    # Get dates from timestamps
    created_at = meeting.get('created_at')
    updated_at = meeting.get('updated_at')
    if created_at:
        # Convert from timestamp to readable date
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(created_at / 1000)  # Assuming milliseconds
            print(f"Date: {dt.strftime('%Y-%m-%d %H:%M')}")
        except:
            print(f"Date: {created_at}")

    # Get people
    people = meeting.get('people', [])
    if people and isinstance(people, list):
        names = [p.get('name', '') for p in people if isinstance(p, dict) and p.get('name')]
        if names:
            print(f"Attendees: {', '.join(names)}")

    # Get overview/summary
    overview = meeting.get('overview', '')
    if overview and isinstance(overview, str) and overview.strip():
        print(f"\nOverview:")
        print(overview[:800] + ("..." if len(overview) > 800 else ""))

    # Get summary
    summary = meeting.get('summary', '')
    if summary and isinstance(summary, str) and summary.strip():
        print(f"\nSummary:")
        print(summary[:800] + ("..." if len(summary) > 800 else ""))

    # Get notes_markdown (preferred format)
    notes_markdown = meeting.get('notes_markdown', '')
    if notes_markdown and isinstance(notes_markdown, str) and notes_markdown.strip():
        print(f"\nNotes:")
        print(notes_markdown[:1500] + ("..." if len(notes_markdown) > 1500 else ""))

    print()
    print()
