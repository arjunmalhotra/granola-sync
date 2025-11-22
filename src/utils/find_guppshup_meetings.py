#!/usr/bin/env python3
import json
import re

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

print("=" * 80)
print("GUPPSHUP-RELATED MEETINGS")
print("=" * 80)
print()

# Search for GuppShup or Aman in various fields
search_terms = ['guppshup', 'gupshup', 'aman']
matches = []

for meeting in documents:
    title = (meeting.get('title') or '').lower()
    notes_markdown = (meeting.get('notes_markdown') or '').lower()
    summary = (meeting.get('summary') or '').lower()
    overview = (meeting.get('overview') or '').lower()

    # Combine all searchable text
    searchable_text = f"{title} {notes_markdown} {summary} {overview}"

    # Check if any search term appears
    if any(term in searchable_text for term in search_terms):
        # Get original (non-lowercased) content
        matches.append({
            'title': meeting.get('title', 'Untitled'),
            'date': meeting.get('created_at', 'Unknown'),
            'people': meeting.get('people', {}),
            'notes_markdown': meeting.get('notes_markdown', ''),
            'summary': meeting.get('summary', ''),
            'overview': meeting.get('overview', ''),
            'relevance': []
        })

        # Track which terms matched
        if 'guppshup' in searchable_text or 'gupshup' in searchable_text:
            matches[-1]['relevance'].append('GuppShup mentioned')
        if 'aman' in searchable_text:
            matches[-1]['relevance'].append('Aman mentioned')

print(f"Found {len(matches)} meetings related to GuppShup/Aman\n")

for i, meeting in enumerate(matches, 1):
    print(f"\n{'=' * 80}")
    print(f"Meeting #{i}")
    print("=" * 80)
    print(f"Title: {meeting['title']}")
    print(f"Date: {meeting['date']}")
    print(f"Relevance: {', '.join(meeting['relevance'])}")

    people = meeting.get('people', {})
    if isinstance(people, dict):
        attendees = people.get('attendees', [])
        if attendees:
            names = [a.get('name', '') for a in attendees if a.get('name')]
            if names:
                print(f"Attendees: {', '.join(names)}")

    # Show content
    if meeting['overview']:
        print(f"\n--- Overview ---")
        print(meeting['overview'])

    if meeting['summary']:
        print(f"\n--- Summary ---")
        print(meeting['summary'])

    if meeting['notes_markdown']:
        print(f"\n--- Notes ---")
        print(meeting['notes_markdown'])

    print()
