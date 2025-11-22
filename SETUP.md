# Setup Guide

Complete installation and configuration instructions for Granola Sync.

## Prerequisites

### System Requirements

- **Operating System:** macOS 10.14 (Mojave) or later
- **Python:** 3.7 or later (included with macOS)
- **Disk Space:** ~50 MB for the repository + ~5 MB per 1000 meetings
- **Granola:** Desktop app installed and signed in

### Check Your Python Version

```bash
python3 --version
```

Should output `Python 3.7.x` or higher.

### Verify Granola Cache Exists

```bash
ls -lh ~/Library/Application\ Support/Granola/cache-v3.json
```

Should show a file (typically 1-10 MB). If not found, open Granola and let it sync.

## Installation

### Step 1: Clone the Repository

```bash
cd ~/Downloads
git clone https://github.com/yourusername/granola-sync.git
cd granola-sync
```

### Step 2: Choose Output Location

**Default:** `~/basic-memory/Granola/`

If you want a different location, edit `src/import-granola-to-memory.py`:

```python
# Line 16
MEMORY_BASE = Path.home() / "basic-memory/Granola"  # Change this path
```

Common alternatives:
- Obsidian vault: `Path.home() / "Documents/Obsidian/Meetings"`
- iCloud: `Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Vault/Granola"`
- Dropbox: `Path.home() / "Dropbox/Notes/Granola"`

### Step 3: Test the Sync Script

```bash
python3 src/import-granola-to-memory.py
```

**Expected Output:**
```
================================================================================
🍯 Granola → Basic Memory Sync
================================================================================

📂 Loading Granola cache...
📅 Last sync: Never
🗂️  Building folder mappings...
   Found 19 folders
   Mapped 340 documents to folders

📊 Found 692 total meetings

... (progress messages) ...

================================================================================
📊 SYNC REPORT
================================================================================

✨ New meetings:        692
🔄 Updated meetings:    0
⏭️  Unchanged meetings:  0
📎 Stub files created:  21
🎤 Transcripts added:   20

📁 Total meetings:      692
📂 Location:            /Users/yourusername/basic-memory/Granola

================================================================================

✅ Sync complete!
```

If you see errors, check [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Step 4: Verify Output

```bash
# Check folder structure
ls ~/basic-memory/Granola/

# View a meeting note
cat ~/basic-memory/Granola/*/2025-*.md | head -50
```

You should see:
- Multiple folders matching your Granola organization
- Markdown files with meeting notes
- `_transcripts/` directory
- `.granola-sync-state.json` file

## Manual Sync Setup

Create a clickable application for triggering syncs.

### Option A: Desktop App (Recommended)

```bash
# Compile AppleScript to application
osacompile -o ~/Desktop/Sync\ Granola.app src/sync-granola.applescript

# Make it executable
chmod +x ~/Desktop/Sync\ Granola.app/Contents/MacOS/applet
```

**Usage:** Double-click "Sync Granola" on your Desktop.

**Customization:** Change the icon
```bash
# Find an icon (PNG or ICNS)
# Right-click Sync Granola.app → Get Info
# Drag icon onto the app icon in the top-left
```

### Option B: Alfred/Raycast Workflow

**Alfred:**
```bash
# Create workflow with "Run Script" action
/usr/bin/python3 ~/granola-sync/src/import-granola-to-memory.py
```

**Raycast:**
```bash
# Create script command
#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Sync Granola
# @raycast.mode fullOutput

python3 ~/granola-sync/src/import-granola-to-memory.py
```

### Option C: Keyboard Shortcut (Automator)

1. Open **Automator** (`Cmd+Space` → "Automator")
2. New Document → **Quick Action**
3. Workflow receives: **no input** in **any application**
4. Add action: **Run Shell Script**
   ```bash
   /usr/bin/python3 $HOME/granola-sync/src/import-granola-to-memory.py
   ```
5. Save as "Sync Granola"
6. System Preferences → Keyboard → Shortcuts → Services
7. Find "Sync Granola" and assign a keyboard shortcut

## Automatic Daily Sync Setup

### Step 1: Copy Python Script to Home Directory

```bash
cp src/import-granola-to-memory.py ~/
```

**Why?** LaunchAgent requires absolute paths, and `~/` is consistent across users.

### Step 2: Verify Python Path

```bash
which python3
```

Expected: `/usr/bin/python3` (system Python)

If different (e.g., `/usr/local/bin/python3` from Homebrew), edit `config/com.granola.sync.plist`:

```xml
<key>ProgramArguments</key>
<array>
    <string>/usr/local/bin/python3</string>  <!-- Update this -->
    <string>/Users/yourusername/import-granola-to-memory.py</string>
</array>
```

### Step 3: Install LaunchAgent

```bash
# Copy plist to LaunchAgents directory
cp config/com.granola.sync.plist ~/Library/LaunchAgents/

# Create log directory
mkdir -p ~/Library/Logs

# Load the agent
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
```

### Step 4: Verify Installation

```bash
# Check if loaded
launchctl list | grep granola

# Should output:
# -	0	com.granola.sync
```

The `-` means it's loaded but not currently running (normal).
The `0` is the last exit status (0 = success).

### Step 5: Test Immediate Run (Optional)

```bash
# Trigger sync immediately (don't wait for 9 AM)
launchctl start com.granola.sync

# Check logs
cat ~/Library/Logs/granola-sync.log
```

## Customization

### Change Sync Schedule

Edit `~/Library/LaunchAgents/com.granola.sync.plist`:

**Daily at 9 PM:**
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>21</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

**Multiple times per day:**
```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key><integer>9</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key><integer>17</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
</array>
```

**Every hour:**
```xml
<key>StartInterval</key>
<integer>3600</integer>  <!-- seconds -->
```

**After changes, reload:**
```bash
launchctl unload ~/Library/LaunchAgents/com.granola.sync.plist
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
```

### Change Output Format

Edit `format_meeting_content()` in `src/import-granola-to-memory.py`:

**Add YAML frontmatter:**
```python
content = f"""---
title: {title}
date: {date_str}
people: {', '.join(people)}
tags: [meeting, granola]
---

# {title}

**Date:** {date_str}
...
"""
```

**Add Obsidian callouts:**
```python
if enhanced_notes:
    content += "\n> [!note] AI-Enhanced Notes\n"
    for panel_title, panel_content in enhanced_notes:
        content += f"> ### {panel_title}\n"
        content += f"> {panel_content}\n\n"
```

**Custom transcript format:**
```python
def format_transcript(transcript_data):
    # Change from:
    # "Speaker: Text"
    # To:
    # "[00:00] Speaker: Text"
    segments = transcript_data.get('segments', [])
    lines = []
    for seg in segments:
        timestamp = format_time(seg.get('start_time', 0))
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '')
        lines.append(f"[{timestamp}] {speaker}: {text}")
    return '\n\n'.join(lines)
```

### Selective Sync (Date Filter)

Edit `main()` to skip old meetings:

```python
from datetime import datetime, timedelta

def main():
    # ... existing code ...

    # Only sync meetings from last 90 days
    cutoff_date = datetime.now() - timedelta(days=90)

    for meeting_id, meeting in meetings.items():
        created_str = meeting.get('created_at', '')
        if created_str:
            created_dt = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
            if created_dt < cutoff_date:
                continue  # Skip old meeting

        # ... rest of sync logic ...
```

### Exclude Certain Folders

```python
EXCLUDED_FOLDERS = ['Personal', 'Wedding Planning']

def should_sync_meeting(folders):
    return not any(f in EXCLUDED_FOLDERS for f in folders)
```

## Integration with Other Tools

### Obsidian

Granola Sync output is fully compatible with Obsidian:

1. **Set output to Obsidian vault:**
   ```python
   MEMORY_BASE = Path.home() / "Documents/Obsidian/MyVault/Meetings"
   ```

2. **Enable wikilinks:** Already using `[[...]]` format

3. **Add to .obsidian/app.json:**
   ```json
   {
     "attachmentFolderPath": "_transcripts"
   }
   ```

### VS Code / Cursor

1. Install Markdown Preview extension
2. Open workspace: `code ~/basic-memory/Granola`
3. Cmd+Shift+V to preview markdown

### Notion (via API)

```python
import requests

def export_to_notion(meeting_content, title):
    # Notion API integration
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]}
        },
        "children": [
            {"object": "block", "type": "paragraph", ...}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
```

### Claude / Claude Code

Already works! Claude Code can read the exported markdown files:

```bash
# In Claude Code
grep -r "specific topic" ~/basic-memory/Granola/
```

## Updating

### Update the Script

```bash
cd ~/granola-sync
git pull origin main

# Re-copy if you modified the home copy
cp src/import-granola-to-memory.py ~/
```

### Update LaunchAgent

```bash
# Unload current
launchctl unload ~/Library/LaunchAgents/com.granola.sync.plist

# Copy new version
cp config/com.granola.sync.plist ~/Library/LaunchAgents/

# Reload
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
```

## Uninstallation

### Remove LaunchAgent

```bash
# Stop and unload
launchctl unload ~/Library/LaunchAgents/com.granola.sync.plist

# Delete plist
rm ~/Library/LaunchAgents/com.granola.sync.plist
```

### Remove Files

```bash
# Delete scripts
rm ~/import-granola-to-memory.py
rm -rf ~/Desktop/Sync\ Granola.app

# Delete repository
rm -rf ~/granola-sync

# Delete exported notes (WARNING: permanent!)
rm -rf ~/basic-memory/Granola
```

### Remove Logs

```bash
rm ~/Library/Logs/granola-sync.log
rm ~/Library/Logs/granola-sync-error.log
```

## Advanced Configuration

### Run as Different User

Edit `config/com.granola.sync.plist`:

```xml
<key>UserName</key>
<string>differentuser</string>
```

### Environment Variables

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin</string>
    <key>GRANOLA_OUTPUT</key>
    <string>/custom/path</string>
</dict>
```

### Success/Failure Notifications

Add to `src/import-granola-to-memory.py`:

```python
import subprocess

def send_notification(title, message):
    subprocess.run([
        'osascript', '-e',
        f'display notification "{message}" with title "{title}"'
    ])

# At end of main()
send_notification("Granola Sync", f"Synced {stats['new']} new meetings")
```

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if issues arise
- Explore utility scripts in `src/utils/`
- Customize output format for your workflow

## Support

If you encounter issues:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review logs: `~/Library/Logs/granola-sync.log`
3. Open an issue on GitHub with:
   - Your macOS version
   - Python version
   - Full error message
   - Relevant log excerpts
