#!/usr/bin/env python3
import json

# Load the cache file
cache_path = "/Users/arjunmalhotra/Library/Application Support/Granola/cache-v3.json"

with open(cache_path, 'r') as f:
    data = json.load(f)

# Double-JSON decoding
cache_data = json.loads(data['cache'])
state = cache_data.get('state', {})

documents_raw = state.get('documents', [])
if isinstance(documents_raw, dict):
    documents = list(documents_raw.values())
else:
    documents = documents_raw

print(f"Total meetings: {len(documents)}")
print("\nLooking for meetings with notes...\n")
print("=" * 80)

count = 0
for meeting in documents:
    # Check if has notes
    notes_markdown = meeting.get('notes_markdown', '')
    summary = meeting.get('summary', '')
    overview = meeting.get('overview', '')

    if (notes_markdown and len(notes_markdown) > 50) or \
       (summary and len(summary) > 50) or \
       (overview and len(overview) > 50):
        count += 1
        if count <= 5:  # Show first 5 meetings with notes
            print(f"\nMeeting #{count}")
            print("-" * 80)
            print(f"Title: {meeting.get('title', 'Untitled')}")
            print(f"Date: {meeting.get('created_at', 'Unknown')}")

            people = meeting.get('people', {})
            if isinstance(people, dict):
                attendees = people.get('attendees', [])
                if attendees:
                    names = [a.get('name', '') for a in attendees if a.get('name')]
                    if names:
                        print(f"Attendees: {', '.join(names)}")

            if overview and len(overview) > 50:
                print(f"\n**Overview:**")
                print(overview[:1000] + ("..." if len(overview) > 1000 else ""))

            if summary and len(summary) > 50:
                print(f"\n**Summary:**")
                print(summary[:1000] + ("..." if len(summary) > 1000 else ""))

            if notes_markdown and len(notes_markdown) > 50:
                print(f"\n**Notes:**")
                print(notes_markdown[:1500] + ("..." if len(notes_markdown) > 1500 else ""))

            print()

print(f"\nTotal meetings with notes: {count}")
