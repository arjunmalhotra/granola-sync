# Architecture Documentation

## System Overview

Granola Sync is a unidirectional synchronization system that extracts meeting notes from Granola's local cache and converts them into organized Markdown files. The system is designed for efficiency, using incremental updates to minimize processing time.

```
┌─────────────────┐
│  Granola App    │
│   (Desktop)     │
└────────┬────────┘
         │ writes to
         ↓
┌─────────────────────────────┐
│  cache-v3.json              │
│  (Application Support)      │
│  - meetings collection      │
│  - documentPanels (AI)      │
│  - documentLists (folders)  │
│  - transcripts              │
└────────┬────────────────────┘
         │ read by
         ↓
┌─────────────────────────────┐
│  import-granola-to-memory.py│
│  - Parse JSON cache         │
│  - TipTap → Markdown        │
│  - Track sync state         │
│  - Incremental updates      │
└────────┬────────────────────┘
         │ writes to
         ↓
┌─────────────────────────────┐
│  Basic Memory Structure     │
│  ~/basic-memory/Granola/    │
│  - Organized folders        │
│  - Markdown meeting notes   │
│  - Transcript files         │
│  - Sync state tracker       │
└─────────────────────────────┘
         │ accessed by
         ↓
┌─────────────────────────────┐
│  Knowledge Management       │
│  - Obsidian / Claude Code   │
│  - Text search / RAG        │
│  - Cross-reference links    │
└─────────────────────────────┘
```

## Data Flow

### 1. Cache Reading

**Location:** `~/Library/Application Support/Granola/cache-v3.json`

**Structure:**
```json
{
  "cache": "{...}",  // Stringified JSON (needs double parsing)
  "version": "3"
}
```

**Parsed State:**
```json
{
  "state": {
    "meetings": {
      "meeting-id-123": {
        "id": "...",
        "title": "Meeting Title",
        "created_at": "2025-11-21T09:46:00Z",
        "updated_at": "2025-11-21T10:30:00Z",
        "notes": {...},  // TipTap JSON (private notes)
        "transcript": {...},
        "people": [...],
        "..."
      }
    },
    "documentPanels": {
      "panel-id-456": {
        "meeting_id": "meeting-id-123",
        "title": "Summary",
        "content": {...}  // TipTap JSON (AI-enhanced)
      }
    },
    "documentLists": {
      "list-id-789": {
        "documents": ["meeting-id-123", "..."]
      }
    },
    "documentListsMetadata": {
      "list-id-789": {
        "name": "Tax Planning",
        "..."
      }
    }
  }
}
```

### 2. Folder Mapping

**Process:**
1. Load `documentListsMetadata` to get folder names
2. Load `documentLists` to get document→folder mappings
3. Create inverted index: `document_id → [folder_names]`

**Code:**
```python
def build_folder_mappings(state):
    # Get folder names
    list_meta = state.get('documentListsMetadata', {})
    folder_names = {
        list_id: data.get('name', 'Unfiled')
        for list_id, data in list_meta.items()
    }

    # Map documents to folders
    doc_lists = state.get('documentLists', {})
    doc_to_folders = defaultdict(list)

    for list_id, list_data in doc_lists.items():
        folder_name = folder_names.get(list_id, 'Unfiled')
        docs = list_data.get('documents', [])
        for doc_id in docs:
            doc_to_folders[doc_id].append(folder_name)

    return doc_to_folders, folder_names
```

### 3. TipTap/ProseMirror Parsing

Granola uses TipTap (based on ProseMirror) for rich text editing. Notes are stored as JSON:

**Input Format:**
```json
{
  "type": "doc",
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Hello "},
        {"type": "text", "text": "world", "marks": [{"type": "bold"}]}
      ]
    },
    {
      "type": "bulletList",
      "content": [
        {
          "type": "listItem",
          "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Item 1"}]}
          ]
        }
      ]
    }
  ]
}
```

**Parser Implementation:**
```python
def parse_tiptap_to_markdown(notes_obj):
    """Recursive parser for TipTap JSON → Markdown"""

    # Supported node types:
    # - paragraph → text + newlines
    # - heading (levels 1-6) → # headers
    # - bulletList/orderedList → - bullets / 1. numbers
    # - listItem → nested items with indentation
    # - codeBlock → ```language blocks
    # - blockquote → > quotes
    # - hardBreak → explicit line breaks

    # Supported marks (inline):
    # - bold → **text**
    # - italic → *text*
    # - code → `text`
    # - link → [text](url)
```

**Key Challenges:**
1. **Nested Lists:** Maintain indentation levels through recursion
2. **Marks Application:** Apply bold/italic to text spans
3. **Empty Nodes:** Handle null/empty content gracefully
4. **List Continuity:** Preserve numbered list sequences

### 4. AI-Enhanced Notes Extraction

**Discovery:** AI-enhanced notes (gray text in Granola) are NOT in `meeting.notes` but in `documentPanels`.

**Mapping:**
```python
# documentPanels structure
{
  "panel-id": {
    "meeting_id": "...",      # Links to meeting
    "title": "Summary",        # Panel section title
    "content": {...},          # TipTap JSON
    "created_at": "...",
    "updated_at": "..."
  }
}

# One meeting can have multiple panels:
# - "Summary"
# - "Action Items"
# - "Key Topics"
# - Custom sections
```

**Extraction Process:**
```python
def format_meeting_content(meeting, doc_panels):
    # 1. Get private/manual notes
    notes_md = parse_tiptap_to_markdown(meeting.get('notes', {}))

    # 2. Get AI-enhanced panels for this meeting
    meeting_id = meeting.get('id')
    enhanced_notes = []

    for panel_id, panel_data in doc_panels.items():
        if panel_data.get('meeting_id') == meeting_id:
            panel_title = panel_data.get('title', '')
            panel_content = parse_tiptap_to_markdown(panel_data.get('content', {}))
            enhanced_notes.append((panel_title, panel_content))

    # 3. Format output
    output = f"# {title}\n\n"
    output += f"**Date:** {date}\n"

    if notes_md:
        output += "\n## Private Notes\n\n" + notes_md

    if enhanced_notes:
        output += "\n## AI-Enhanced Notes\n\n"
        for title, content in enhanced_notes:
            if title:
                output += f"### {title}\n\n"
            output += content + "\n\n"

    return output
```

### 5. Incremental Sync Mechanism

**State Tracking File:** `.granola-sync-state.json`

```json
{
  "last_sync": "2025-11-22T15:41:38.123456",
  "meetings": {
    "meeting-id-123": {
      "title": "Meeting Title",
      "updated_at": "2025-11-21T10:30:00Z",
      "folders": ["Tax Planning", "Finance"],
      "file_path": "Tax Planning/2025-11-21_Meeting_Title.md"
    }
  }
}
```

**Update Logic:**
```python
def needs_update(meeting, sync_state):
    meeting_id = meeting['id']

    # New meeting?
    if meeting_id not in sync_state['meetings']:
        return True

    # Check update timestamp
    current_updated = meeting.get('updated_at')
    previous_updated = sync_state['meetings'][meeting_id].get('updated_at')

    if current_updated != previous_updated:
        return True

    return False
```

**Performance:**
- Average run (no changes): ~2 seconds for 700 meetings
- With updates: ~0.5 seconds per changed meeting
- Full re-sync (--force): ~30 seconds for 700 meetings

### 6. Multi-Folder Handling

**Challenge:** Meetings can appear in multiple Granola folders (e.g., "Tax Planning" + "Finance")

**Solution:** Primary file + stub files

```
Primary File (first folder):
~/basic-memory/Granola/Tax Planning/2025-11-21_Meeting.md
[Full content]

Stub File (additional folders):
~/basic-memory/Granola/Finance/2025-11-21_Meeting.md
→ See: [[../Tax Planning/2025-11-21_Meeting]]
```

**Implementation:**
```python
def create_stub_file(target_path, primary_path):
    """Create stub file pointing to primary"""
    rel_path = os.path.relpath(primary_path, target_path.parent)
    # Remove .md extension for wiki-style link
    rel_path_no_ext = rel_path.replace('.md', '')

    stub_content = f"→ See: [[{rel_path_no_ext}]]\n"
    target_path.write_text(stub_content)
```

**Benefits:**
- Find meetings in all relevant contexts
- No content duplication
- Updates only touch primary file
- Wiki-style links work in Obsidian

### 7. Transcript Handling

**Transcript Structure:**
```json
{
  "segments": [
    {
      "speaker": "Arjun",
      "text": "Let's discuss...",
      "start_time": 0.0,
      "end_time": 3.5
    },
    {
      "speaker": "Hugh",
      "text": "Sounds good...",
      "start_time": 3.5,
      "end_time": 7.2
    }
  ]
}
```

**Export Format:**
```
Arjun: Let's discuss...

Hugh: Sounds good...

Arjun: Following up on...
```

**Storage:**
```
~/basic-memory/Granola/_transcripts/
├── 2025-11-21_Meeting_Title_transcript.txt
└── 2025-11-20_Another_Meeting_transcript.txt
```

**Linking:**
Meeting notes include: `[[_transcripts/2025-11-21_Meeting_Title_transcript.txt]]`

## Automation Architecture

### AppleScript Wrapper

**Purpose:** User-friendly manual trigger with visual feedback

**Flow:**
1. User double-clicks "Sync Granola.app"
2. AppleScript shows notification: "Starting..."
3. Runs: `/usr/bin/python3 ~/import-granola-to-memory.py`
4. Captures stdout
5. Parses output for meeting counts (strips ANSI codes)
6. Shows completion notification with summary
7. Error handling with visual alerts

**Key Feature:** ANSI color code stripping
```applescript
-- Strip color codes before parsing
set cleanOutput to do shell script "echo " & quoted form of output &
    " | sed 's/\\x1b\\[[0-9;]*m//g'"
```

### LaunchAgent (Daily Automation)

**plist Configuration:**
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key><integer>9</integer>
    <key>Minute</key><integer>0</integer>
</dict>
```

**Logging:**
- stdout → `~/Library/Logs/granola-sync.log`
- stderr → `~/Library/Logs/granola-sync-error.log`

**Management:**
```bash
# Load
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist

# Unload
launchctl unload ~/Library/LaunchAgents/com.granola.sync.plist

# Check status
launchctl list | grep granola

# View logs
tail -f ~/Library/Logs/granola-sync.log
```

## Code Organization

### Main Script (`import-granola-to-memory.py`)

**Functions:**

1. **Data Loading**
   - `load_granola_data()` - Parse cache JSON
   - `load_sync_state()` - Load previous state
   - `save_sync_state()` - Persist state

2. **Parsing**
   - `parse_tiptap_to_markdown()` - Convert rich text
   - `parse_tiptap_node()` - Handle node types
   - `apply_marks()` - Apply inline formatting

3. **Mapping**
   - `build_folder_mappings()` - Document→folder index
   - `safe_filename()` - Sanitize file names
   - `format_date()` - Timestamp formatting

4. **Content Generation**
   - `format_meeting_content()` - Build markdown output
   - `extract_people()` - Parse attendee data
   - `format_transcript()` - Convert transcript to text

5. **Sync Logic**
   - `needs_update()` - Check if meeting changed
   - `sync_meeting()` - Write primary file
   - `create_stub_file()` - Create folder links
   - `main()` - Orchestrate sync process

**Control Flow:**
```python
def main():
    # 1. Load data
    state = load_granola_data()
    sync_state = load_sync_state()

    # 2. Build mappings
    doc_to_folders = build_folder_mappings(state)

    # 3. Process meetings
    for meeting in state['meetings'].values():
        if needs_update(meeting, sync_state):
            sync_meeting(meeting, doc_to_folders)
            stats['updated'] += 1

    # 4. Save state
    save_sync_state(sync_state)

    # 5. Print report
    print_stats(stats)
```

## Performance Considerations

### Optimization Strategies

1. **Incremental Updates Only**
   - Check `updated_at` before processing
   - Skip unchanged meetings
   - ~100x faster than full re-sync

2. **Single Cache Read**
   - Load entire cache once
   - Build all mappings upfront
   - No repeated file I/O

3. **Lazy Transcript Writing**
   - Only write if transcript exists
   - Only update if transcript changed

4. **State Minimization**
   - Only track essential fields
   - Use ISO timestamps (compact)
   - Don't duplicate content

### Benchmarks

**Dataset:** 692 meetings, 3.6 MB output

| Operation | Time | Notes |
|-----------|------|-------|
| Cold start (full sync) | ~30s | All 692 meetings |
| Incremental (no changes) | ~2s | Just reads cache |
| Incremental (5 updates) | ~4s | Only processes changed |
| TipTap parsing | ~50ms per meeting | Depends on content size |
| File write | ~10ms per file | SSD performance |

## Security & Privacy

### Data Flow
- **Local only:** Never uploads to external servers
- **Read-only:** Doesn't modify Granola cache
- **No network:** Pure file system operations

### Sensitive Data
- Meeting transcripts may contain confidential information
- Exported files inherit Granola's data sensitivity
- Recommend: Encrypt `~/basic-memory/` if needed

### Permissions
- Read: `~/Library/Application Support/Granola/`
- Write: `~/basic-memory/Granola/`
- Execute: Python scripts

## Error Handling

### Graceful Degradation

1. **Missing Cache**
   ```python
   if not GRANOLA_CACHE.exists():
       log("❌ Granola cache not found", Colors.RED)
       sys.exit(1)
   ```

2. **Malformed JSON**
   ```python
   try:
       data = json.load(f)
   except json.JSONDecodeError:
       log("❌ Invalid cache format", Colors.RED)
       sys.exit(1)
   ```

3. **Missing Fields**
   ```python
   title = meeting.get('title') or "Untitled"
   notes = meeting.get('notes', {})  # Default empty
   ```

4. **File System Errors**
   ```python
   try:
       output_path.write_text(content)
   except IOError as e:
       log(f"❌ Failed to write: {e}", Colors.RED)
       continue  # Skip this meeting, continue with others
   ```

### Logging Strategy

- **Colors for clarity:** Green (success), Blue (info), Yellow (warning), Red (error)
- **Progress indicators:** Show current operation
- **Summary statistics:** Report at end
- **Error details:** Full stack traces in logs

## Future Enhancements

### Potential Improvements

1. **Bidirectional Sync**
   - Watch file system for changes
   - Update Granola cache (complex, risky)

2. **Cloud Sync Support**
   - Use Granola API instead of local cache
   - Enable sync from any machine

3. **Selective Sync**
   - Filter by date range
   - Filter by folder
   - Exclude certain meetings

4. **Custom Templates**
   - User-defined markdown format
   - Jinja2 template engine
   - Per-folder templates

5. **Rich Export Formats**
   - HTML output
   - PDF generation
   - Notion/Confluence API

6. **Search Index**
   - Build full-text search
   - Tag extraction
   - Cross-reference graph

## References

- **Granola:** https://www.granola.so
- **TipTap:** https://tiptap.dev
- **ProseMirror:** https://prosemirror.net
- **Basic Memory:** Custom knowledge management system
- **Obsidian:** https://obsidian.md (compatible)
