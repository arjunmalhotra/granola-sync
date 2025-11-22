#!/usr/bin/env python3
"""
Complete Granola Data Extractor
Extracts ALL data from Granola's local cache including transcripts, notes, and metadata
"""

import json
import os
from pathlib import Path
from datetime import datetime
import sys

# Paths
GRANOLA_CACHE = Path.home() / "Library/Application Support/Granola/cache-v3.json"
OUTPUT_DIR = Path.home() / "granola-full-export"

def load_granola_data():
    """Load and parse the Granola cache file"""
    print("📂 Loading Granola cache...")
    with open(GRANOLA_CACHE, 'r') as f:
        data = json.load(f)

    # Parse nested JSON
    cache = json.loads(data['cache'])
    state = cache['state']

    return state

def format_date(date_str):
    """Convert ISO date to readable format"""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def safe_filename(name):
    """Create safe filename from title"""
    if not name:
        return "untitled"
    # Remove invalid characters
    safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    # Limit length
    return safe[:100] if safe else "untitled"

def extract_transcript(transcript_data, doc_id):
    """Extract transcript text from transcript data"""
    if not transcript_data:
        return None

    # Transcripts might be a list of segments
    if isinstance(transcript_data, list):
        segments = []
        for segment in transcript_data:
            if isinstance(segment, dict):
                speaker = segment.get('speaker', 'Unknown')
                text = segment.get('text', segment.get('content', ''))
                timestamp = segment.get('timestamp', '')
                if text:
                    segments.append(f"[{speaker}] {text}")
        return "\n\n".join(segments) if segments else None

    # Or it might be a string
    elif isinstance(transcript_data, str):
        return transcript_data

    return None

def export_documents(state, output_dir):
    """Export all documents with full data"""
    documents = state.get('documents', {})
    transcripts = state.get('transcripts', {})

    if not documents:
        print("❌ No documents found")
        return

    print(f"📝 Found {len(documents)} documents")
    print(f"🎤 Found {len(transcripts)} transcripts")

    # Create output directories
    docs_dir = output_dir / "documents"
    transcripts_dir = output_dir / "transcripts"
    metadata_dir = output_dir / "metadata"

    for dir_path in [docs_dir, transcripts_dir, metadata_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Export each document
    exported_count = 0
    skipped_count = 0

    for doc_id, doc in documents.items():
        # Skip deleted documents
        if doc.get('deleted_at'):
            skipped_count += 1
            continue

        title = doc.get('title', 'Untitled')
        created_at = doc.get('created_at', '')

        # Create safe filename
        date_prefix = format_date(created_at).split()[0] if created_at else 'unknown-date'
        filename = f"{date_prefix}_{safe_filename(title)}"

        # Export markdown notes
        notes_markdown = doc.get('notes_markdown', '')
        notes_plain = doc.get('notes_plain', '')

        if notes_markdown or notes_plain:
            with open(docs_dir / f"{filename}.md", 'w') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**Created:** {format_date(created_at)}\n")

                # People
                people = doc.get('people', [])
                if people:
                    if isinstance(people, list):
                        people_names = []
                        for p in people:
                            if isinstance(p, dict):
                                people_names.append(p.get('name', 'Unknown'))
                            elif isinstance(p, str):
                                people_names.append(p)
                        if people_names:
                            f.write(f"**People:** {', '.join(people_names)}\n")
                    elif isinstance(people, str):
                        f.write(f"**People:** {people}\n")

                # Summary
                summary = doc.get('summary', '')
                if summary:
                    f.write(f"\n## Summary\n\n{summary}\n")

                # Notes
                f.write(f"\n## Notes\n\n")
                f.write(notes_markdown or notes_plain or "No notes")

        # Export transcript if available
        transcript_ref = doc.get('transcribe')
        if transcript_ref and transcripts:
            # Try to find matching transcript
            # Transcripts might be indexed by doc_id or by a separate ID
            transcript_content = None

            # Check if transcripts is a dict
            if isinstance(transcripts, dict):
                transcript_content = transcripts.get(doc_id) or transcripts.get(transcript_ref)

            if transcript_content:
                transcript_text = extract_transcript(transcript_content, doc_id)
                if transcript_text:
                    with open(transcripts_dir / f"{filename}_transcript.txt", 'w') as f:
                        f.write(f"Transcript: {title}\n")
                        f.write(f"Created: {format_date(created_at)}\n")
                        f.write(f"\n{'-'*80}\n\n")
                        f.write(transcript_text)

        # Export full metadata as JSON
        with open(metadata_dir / f"{filename}_metadata.json", 'w') as f:
            json.dump(doc, f, indent=2)

        exported_count += 1
        if exported_count % 50 == 0:
            print(f"  Exported {exported_count} documents...")

    print(f"\n✅ Exported {exported_count} documents")
    print(f"⏭️  Skipped {skipped_count} deleted documents")

    # Export raw transcripts
    if transcripts:
        print(f"\n🎤 Exporting raw transcripts...")
        raw_transcripts_file = output_dir / "raw_transcripts.json"
        with open(raw_transcripts_file, 'w') as f:
            json.dump(transcripts, f, indent=2)
        print(f"   Saved to: {raw_transcripts_file}")

def export_people(state, output_dir):
    """Export people/contacts"""
    people = state.get('people', {})

    if not people:
        return

    print(f"\n👥 Found {len(people)} people")

    people_file = output_dir / "people.json"
    with open(people_file, 'w') as f:
        json.dump(people, f, indent=2)

    print(f"   Saved to: {people_file}")

def export_events(state, output_dir):
    """Export calendar events"""
    events = state.get('events', {})

    if not events:
        return

    print(f"\n📅 Found {len(events)} calendar events")

    events_file = output_dir / "calendar_events.json"
    with open(events_file, 'w') as f:
        json.dump(events, f, indent=2)

    print(f"   Saved to: {events_file}")

def create_index(output_dir):
    """Create an index of all exported documents"""
    docs_dir = output_dir / "documents"

    if not docs_dir.exists():
        return

    md_files = sorted(docs_dir.glob("*.md"))

    index_file = output_dir / "INDEX.md"
    with open(index_file, 'w') as f:
        f.write("# Granola Export Index\n\n")
        f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"**Total Documents:** {len(md_files)}\n\n")
        f.write("## Documents\n\n")

        for md_file in md_files:
            # Read first line (title)
            with open(md_file, 'r') as doc:
                first_line = doc.readline().strip()
                title = first_line.replace('# ', '')

            rel_path = md_file.relative_to(output_dir)
            f.write(f"- [{title}]({rel_path})\n")

    print(f"\n📋 Created index: {index_file}")

def main():
    print("=" * 80)
    print("🍯 Granola Complete Data Extractor")
    print("=" * 80)
    print()

    # Check if cache exists
    if not GRANOLA_CACHE.exists():
        print(f"❌ Granola cache not found at: {GRANOLA_CACHE}")
        print("   Make sure Granola is installed and has been run at least once.")
        sys.exit(1)

    # Load data
    state = load_granola_data()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory: {OUTPUT_DIR}\n")

    # Export everything
    export_documents(state, OUTPUT_DIR)
    export_people(state, OUTPUT_DIR)
    export_events(state, OUTPUT_DIR)
    create_index(OUTPUT_DIR)

    print("\n" + "=" * 80)
    print("✨ Export complete!")
    print("=" * 80)
    print(f"\nYour Granola data is in: {OUTPUT_DIR}")
    print(f"\n📖 View the index: open {OUTPUT_DIR}/INDEX.md")
    print(f"📁 Browse documents: open {OUTPUT_DIR}/documents")
    print(f"🎤 Browse transcripts: open {OUTPUT_DIR}/transcripts")
    print()

if __name__ == "__main__":
    main()
