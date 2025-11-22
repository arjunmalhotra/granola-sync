#!/usr/bin/env python3
"""
Granola to Basic Memory Importer
Syncs meetings from Granola into Basic Memory with smart incremental updates
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys

# Paths
GRANOLA_CACHE = Path.home() / "Library/Application Support/Granola/cache-v3.json"
MEMORY_BASE = Path.home() / "basic-memory/Granola"
STATE_FILE = MEMORY_BASE / ".granola-sync-state.json"
TRANSCRIPTS_DIR = MEMORY_BASE / "_transcripts"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, color=None):
    """Print colored log message"""
    if color:
        print(f"{color}{msg}{Colors.END}")
    else:
        print(msg)

def load_granola_data():
    """Load and parse Granola cache"""
    log("📂 Loading Granola cache...", Colors.BLUE)

    if not GRANOLA_CACHE.exists():
        log(f"❌ Granola cache not found at: {GRANOLA_CACHE}", Colors.RED)
        sys.exit(1)

    with open(GRANOLA_CACHE, 'r') as f:
        data = json.load(f)

    cache = json.loads(data['cache'])
    state = cache['state']

    return state

def load_sync_state():
    """Load previous sync state"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_sync": None,
        "meetings": {}
    }

def save_sync_state(state):
    """Save sync state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def format_date(date_str):
    """Convert ISO date to readable format"""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def safe_filename(name, date_str=None):
    """Create safe filename from title"""
    if not name:
        name = "Untitled"

    # Create date prefix
    prefix = ""
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            prefix = dt.strftime('%Y-%m-%d_')
        except:
            pass

    # Remove invalid characters
    safe = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe = safe[:80] if safe else "untitled"  # Limit length

    return f"{prefix}{safe}"

def build_folder_mappings(state):
    """Build mappings between documents, folders, and metadata"""
    log("🗂️  Building folder mappings...", Colors.BLUE)

    # Get folder metadata
    folder_metadata = state.get('documentListsMetadata', {})

    # Get document-to-folder mappings
    document_lists = state.get('documentLists', {})

    # Build reverse mapping: doc_id -> [folder_ids]
    doc_to_folders = defaultdict(list)
    for folder_id, doc_ids in document_lists.items():
        if isinstance(doc_ids, list):
            for doc_id in doc_ids:
                doc_to_folders[doc_id].append(folder_id)

    # Build folder name mapping
    folder_names = {}
    for folder_id, metadata in folder_metadata.items():
        folder_names[folder_id] = metadata.get('title', 'Unknown Folder')

    log(f"   Found {len(folder_metadata)} folders", Colors.GREEN)
    log(f"   Mapped {len(doc_to_folders)} documents to folders", Colors.GREEN)

    return doc_to_folders, folder_names, folder_metadata

def get_meeting_folders(doc_id, doc_to_folders, folder_names):
    """Get list of folder names for a document"""
    folder_ids = doc_to_folders.get(doc_id, [])
    return [folder_names.get(fid, 'Unknown') for fid in folder_ids]

def parse_tiptap_to_markdown(notes_obj):
    """Parse TipTap/ProseMirror JSON format to markdown"""
    if not notes_obj or not isinstance(notes_obj, dict):
        return ""

    content = notes_obj.get('content', [])
    if not isinstance(content, list):
        return ""

    def parse_node(node, indent=0):
        """Recursively parse a TipTap node"""
        if not isinstance(node, dict):
            return ""

        node_type = node.get('type', '')
        node_content = node.get('content', [])

        result = []
        indent_str = "  " * indent

        if node_type == 'paragraph':
            # Extract text from paragraph
            text_parts = []
            for child in node_content:
                if isinstance(child, dict):
                    if child.get('type') == 'text':
                        text = child.get('text', '')
                        # Handle marks (bold, italic, etc.)
                        marks = child.get('marks', [])
                        for mark in marks:
                            if isinstance(mark, dict):
                                mark_type = mark.get('type')
                                if mark_type == 'bold':
                                    text = f"**{text}**"
                                elif mark_type == 'italic':
                                    text = f"*{text}*"
                                elif mark_type == 'code':
                                    text = f"`{text}`"
                        text_parts.append(text)

            if text_parts:
                result.append(''.join(text_parts))

        elif node_type == 'heading':
            level = node.get('attrs', {}).get('level', 1)
            heading_prefix = '#' * level
            text_parts = []
            for child in node_content:
                if isinstance(child, dict) and child.get('type') == 'text':
                    text_parts.append(child.get('text', ''))
            if text_parts:
                result.append(f"{heading_prefix} {' '.join(text_parts)}")

        elif node_type == 'bulletList':
            for item in node_content:
                if isinstance(item, dict) and item.get('type') == 'listItem':
                    item_content = item.get('content', [])
                    for para in item_content:
                        if isinstance(para, dict):
                            para_text = parse_node(para, indent)
                            if para_text:
                                result.append(f"{indent_str}- {para_text}")
                            # Handle nested lists
                            nested = para.get('content', [])
                            for nested_node in nested:
                                if isinstance(nested_node, dict) and nested_node.get('type') in ['bulletList', 'orderedList']:
                                    result.append(parse_node(nested_node, indent + 1))

        elif node_type == 'orderedList':
            for idx, item in enumerate(node_content, 1):
                if isinstance(item, dict) and item.get('type') == 'listItem':
                    item_content = item.get('content', [])
                    for para in item_content:
                        if isinstance(para, dict):
                            para_text = parse_node(para, indent)
                            if para_text:
                                result.append(f"{indent_str}{idx}. {para_text}")

        elif node_type == 'codeBlock':
            code_lines = []
            for child in node_content:
                if isinstance(child, dict) and child.get('type') == 'text':
                    code_lines.append(child.get('text', ''))
            if code_lines:
                result.append("```")
                result.extend(code_lines)
                result.append("```")

        elif node_type == 'blockquote':
            for child in node_content:
                if isinstance(child, dict):
                    child_text = parse_node(child, indent)
                    if child_text:
                        result.append(f"> {child_text}")

        elif node_type == 'horizontalRule':
            result.append("---")

        return '\n'.join(result) if result else ''

    # Parse all top-level nodes
    markdown_parts = []
    for node in content:
        parsed = parse_node(node)
        if parsed:
            markdown_parts.append(parsed)

    return '\n\n'.join(markdown_parts)

def format_meeting_content(doc, folders, primary_folder, transcript_filename=None, doc_panels=None):
    """Format meeting note content"""
    title = doc.get('title', 'Untitled Meeting')
    created = doc.get('created_at', '')
    summary = doc.get('summary', '')

    # Try to get notes from multiple sources
    notes_md = doc.get('notes_markdown', '')
    notes_plain = doc.get('notes_plain', '')

    # If markdown/plain are empty, parse the TipTap JSON structure
    if not notes_md and not notes_plain:
        notes_obj = doc.get('notes', {})
        if notes_obj:
            notes_md = parse_tiptap_to_markdown(notes_obj)

    # Parse AI-enhanced panels
    enhanced_notes = []
    if doc_panels:
        for panel_id, panel_data in doc_panels.items():
            if isinstance(panel_data, dict):
                panel_title = panel_data.get('title', '')
                panel_content = panel_data.get('content', {})
                if panel_content:
                    panel_md = parse_tiptap_to_markdown(panel_content)
                    if panel_md:
                        enhanced_notes.append((panel_title, panel_md))

    # People
    people_list = []
    people = doc.get('people', {})
    if isinstance(people, dict):
        attendees = people.get('attendees', [])
        if isinstance(attendees, list):
            for person in attendees:
                if isinstance(person, dict):
                    name = person.get('name') or person.get('email', '')
                    if name:
                        people_list.append(name)

    # Granola link
    metadata = doc.get('metadata', {})
    if isinstance(metadata, dict):
        granola_url = metadata.get('url', '')
    else:
        granola_url = ''

    # Build content
    content = f"# {title}\n\n"
    content += f"**Date:** {format_date(created)}\n"
    content += f"**Primary Folder:** {primary_folder}\n"

    if len(folders) > 1:
        other_folders = [f for f in folders if f != primary_folder]
        content += f"**Also in:** {', '.join(other_folders)}\n"

    if people_list:
        content += f"**People:** {', '.join(people_list)}\n"

    if granola_url:
        content += f"**Granola:** [View in app]({granola_url})\n"

    # Summary
    if summary:
        content += f"\n## Summary\n\n{summary}\n"

    # Manual/Private Notes
    if notes_md or notes_plain:
        content += f"\n## Private Notes\n\n"
        content += notes_md or notes_plain
    elif not enhanced_notes:
        content += f"\n## Notes\n\n*No notes recorded*\n"

    # AI-Enhanced Notes (from panels)
    if enhanced_notes:
        content += f"\n## AI-Enhanced Notes\n\n"
        for panel_title, panel_content in enhanced_notes:
            if panel_title:
                content += f"### {panel_title}\n\n"
            content += panel_content + "\n\n"

    # Transcript link
    if transcript_filename:
        content += f"\n## Transcript\n\n[[_transcripts/{transcript_filename}]]\n"

    return content

def create_stub_file(title, primary_path, date_str, also_in_folders):
    """Create stub file that links to primary location"""
    content = f"# {title}\n\n"
    content += f"→ **This meeting is located in:** [[{primary_path}]]\n\n"
    content += f"**Date:** {format_date(date_str)}\n"

    if also_in_folders:
        content += f"**Also filed in:** {', '.join(also_in_folders)}\n"

    content += f"\n---\n\n"
    content += f"[View full meeting →]({primary_path})\n"

    return content

def extract_transcript(transcript_data, doc_id):
    """Extract transcript text from transcript data"""
    if not transcript_data:
        return None

    if isinstance(transcript_data, list):
        if len(transcript_data) == 0:
            return None

        segments = []
        for segment in transcript_data:
            if isinstance(segment, dict):
                text = segment.get('text', '')
                speaker = segment.get('speaker', None)

                if text:
                    if speaker:
                        segments.append(f"[{speaker}] {text}")
                    else:
                        segments.append(text)

        return "\n\n".join(segments) if segments else None

    return None

def sync_meetings(state, sync_state, force=False):
    """Sync meetings from Granola to Basic Memory"""
    documents = state.get('documents', {})
    transcripts = state.get('transcripts', {})
    document_panels = state.get('documentPanels', {})

    doc_to_folders, folder_names, folder_metadata = build_folder_mappings(state)

    log(f"\n📊 Found {len(documents)} total meetings", Colors.BOLD)

    # Stats
    stats = {
        'new': 0,
        'updated': 0,
        'unchanged': 0,
        'folders_added': 0,
        'folders_removed': 0,
        'stubs_created': 0,
        'stubs_deleted': 0,
        'transcripts_added': 0
    }

    # Create base directory
    MEMORY_BASE.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Process each document
    for doc_id, doc in documents.items():
        # Skip deleted
        if doc.get('deleted_at'):
            continue

        title = doc.get('title', 'Untitled')
        created_at = doc.get('created_at', '')
        updated_at = doc.get('updated_at', created_at)

        # Get folders for this meeting
        folders = get_meeting_folders(doc_id, doc_to_folders, folder_names)
        if not folders:
            folders = ['Unfiled']

        primary_folder = folders[0]
        additional_folders = folders[1:] if len(folders) > 1 else []

        # Check if this is new or updated
        prev_state = sync_state['meetings'].get(doc_id, {})
        is_new = not prev_state

        if not force and not is_new:
            # Check if content changed
            if prev_state.get('last_updated_granola') == updated_at:
                # Check if folders changed
                prev_folders = set(prev_state.get('all_folders', []))
                curr_folders = set(folders)

                if prev_folders == curr_folders:
                    stats['unchanged'] += 1
                    continue

        # Create filename
        filename = safe_filename(title, created_at) + ".md"

        # Create primary folder directory
        primary_dir = MEMORY_BASE / primary_folder
        primary_dir.mkdir(parents=True, exist_ok=True)
        primary_file = primary_dir / filename

        # Check for transcript
        transcript_filename = None
        transcript_content = None
        transcript_data = transcripts.get(doc_id)

        if transcript_data:
            transcript_content = extract_transcript(transcript_data, doc_id)
            if transcript_content:
                transcript_filename = safe_filename(title, created_at) + "_transcript.txt"
                transcript_file = TRANSCRIPTS_DIR / transcript_filename

                # Write transcript
                with open(transcript_file, 'w') as f:
                    f.write(f"Transcript: {title}\n")
                    f.write(f"Date: {format_date(created_at)}\n")
                    f.write(f"\n{'-'*80}\n\n")
                    f.write(transcript_content)

                stats['transcripts_added'] += 1

        # Get AI-enhanced panels for this document
        doc_panels = document_panels.get(doc_id, {})

        # Write primary file
        content = format_meeting_content(doc, folders, primary_folder, transcript_filename, doc_panels)
        with open(primary_file, 'w') as f:
            f.write(content)

        if is_new:
            stats['new'] += 1
        else:
            stats['updated'] += 1

        # Create/update stub files in additional folders
        for add_folder in additional_folders:
            stub_dir = MEMORY_BASE / add_folder
            stub_dir.mkdir(parents=True, exist_ok=True)
            stub_file = stub_dir / filename

            # Relative path from stub to primary
            rel_path = f"../{primary_folder}/{filename}"

            stub_content = create_stub_file(title, rel_path, created_at, additional_folders)
            with open(stub_file, 'w') as f:
                f.write(stub_content)

            stats['stubs_created'] += 1

        # Update sync state
        sync_state['meetings'][doc_id] = {
            'title': title,
            'primary_folder': primary_folder,
            'all_folders': folders,
            'last_updated_granola': updated_at,
            'imported_at': datetime.now().isoformat()
        }

    # Update last sync time
    sync_state['last_sync'] = datetime.now().isoformat()

    return stats

def print_report(stats):
    """Print sync report"""
    log("\n" + "="*80, Colors.BOLD)
    log("📊 SYNC REPORT", Colors.BOLD)
    log("="*80, Colors.BOLD)

    log(f"\n✨ New meetings:        {stats['new']}", Colors.GREEN)
    log(f"🔄 Updated meetings:    {stats['updated']}", Colors.BLUE)
    log(f"⏭️  Unchanged meetings:  {stats['unchanged']}", Colors.YELLOW)
    log(f"📎 Stub files created:  {stats['stubs_created']}", Colors.GREEN)
    log(f"🎤 Transcripts added:   {stats['transcripts_added']}", Colors.GREEN)

    total = stats['new'] + stats['updated'] + stats['unchanged']
    log(f"\n📁 Total meetings:      {total}", Colors.BOLD)
    log(f"📂 Location:            {MEMORY_BASE}", Colors.BOLD)

    log("\n" + "="*80, Colors.BOLD)

def main():
    """Main entry point"""
    log("\n" + "="*80, Colors.BOLD)
    log("🍯 Granola → Basic Memory Sync", Colors.BOLD)
    log("="*80 + "\n", Colors.BOLD)

    # Check for force flag
    force = '--force' in sys.argv
    if force:
        log("⚠️  Force mode: Re-importing all meetings", Colors.YELLOW)

    # Load data
    state = load_granola_data()
    sync_state = load_sync_state()

    if sync_state.get('last_sync'):
        log(f"📅 Last sync: {sync_state['last_sync'][:19]}", Colors.BLUE)
    else:
        log("📅 First sync - importing all meetings", Colors.BLUE)

    # Sync
    stats = sync_meetings(state, sync_state, force)

    # Save state
    save_sync_state(sync_state)

    # Print report
    print_report(stats)

    log("\n✅ Sync complete!\n", Colors.GREEN)

if __name__ == "__main__":
    main()
