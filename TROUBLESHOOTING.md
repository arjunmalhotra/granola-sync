# Troubleshooting Guide

Common issues and their solutions for Granola Sync.

## Quick Diagnostics

Run these commands to diagnose most issues:

```bash
# 1. Check if Granola cache exists
ls -lh ~/Library/Application\ Support/Granola/cache-v3.json

# 2. Check Python version
python3 --version

# 3. Test sync script directly
python3 ~/import-granola-to-memory.py

# 4. Check LaunchAgent status
launchctl list | grep granola

# 5. View recent logs
tail -50 ~/Library/Logs/granola-sync.log
```

## Common Issues

### 1. "Granola cache not found"

**Error:**
```
❌ Granola cache not found at: /Users/you/Library/Application Support/Granola/cache-v3.json
```

**Causes:**
- Granola app not installed
- Granola not signed in
- Different cache location

**Solutions:**

**A. Install/Open Granola**
```bash
# Check if Granola is installed
ls /Applications/Granola.app

# If not found, download from: https://www.granola.so
# Open Granola and sign in
```

**B. Check Alternate Cache Locations**
```bash
find ~/Library -name "cache*.json" -path "*/Granola/*" 2>/dev/null
```

If found at different location, edit `GRANOLA_CACHE` in script:
```python
GRANOLA_CACHE = Path.home() / "Library/Application Support/Granola/cache-v2.json"
```

**C. Force Granola to Create Cache**
1. Open Granola app
2. Click "Sync" button
3. Wait 30 seconds
4. Check if cache exists: `ls -lh ~/Library/Application\ Support/Granola/cache-v3.json`

---

### 2. "Invalid JSON" or "JSONDecodeError"

**Error:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Causes:**
- Corrupted cache file
- Granola sync in progress
- Empty/partial cache

**Solutions:**

**A. Wait for Granola Sync to Complete**
```bash
# Check if Granola is actively syncing
ps aux | grep Granola
```

Wait 1-2 minutes, then try again.

**B. Check Cache File Size**
```bash
ls -lh ~/Library/Application\ Support/Granola/cache-v3.json
```

If 0 bytes or very small (<100 KB), cache may be empty:
1. Open Granola
2. Force refresh (Cmd+R)
3. Wait for sync

**C. Backup and Reset Cache**
```bash
# Backup current cache
cp ~/Library/Application\ Support/Granola/cache-v3.json ~/cache-backup.json

# Quit Granola completely
killall Granola

# Reopen Granola
open /Applications/Granola.app

# Let it re-sync (wait 2-3 minutes)
```

---

### 3. "Permission denied" Errors

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/Users/you/basic-memory/Granola'
```

**Causes:**
- Output directory not writable
- Wrong user running script
- macOS security restrictions

**Solutions:**

**A. Check Directory Permissions**
```bash
ls -ld ~/basic-memory/Granola/

# Should show: drwxr-xr-x (readable and writable by you)
```

Fix permissions:
```bash
chmod 755 ~/basic-memory/Granola/
```

**B. Create Directory Manually**
```bash
mkdir -p ~/basic-memory/Granola
```

**C. Grant Full Disk Access (macOS Catalina+)**
1. System Preferences → Security & Privacy → Privacy
2. Select "Full Disk Access"
3. Click lock to make changes
4. Add Terminal.app or iTerm.app
5. Restart Terminal

---

### 4. LaunchAgent Not Running

**Symptoms:**
- No automatic syncs at 9 AM
- `launchctl list | grep granola` returns nothing
- No log files created

**Solutions:**

**A. Check if LaunchAgent is Loaded**
```bash
launchctl list | grep com.granola.sync
```

If empty, load it:
```bash
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
```

**B. Verify plist Syntax**
```bash
plutil -lint ~/Library/LaunchAgents/com.granola.sync.plist
```

Should output: `OK`

If errors, fix XML syntax in the file.

**C. Check Python Path in plist**
```bash
# Find your Python
which python3

# Should match ProgramArguments in plist
grep -A 5 "ProgramArguments" ~/Library/LaunchAgents/com.granola.sync.plist
```

If different, edit plist:
```xml
<string>/usr/local/bin/python3</string>  <!-- Update to match your python3 -->
```

**D. Force Immediate Run**
```bash
# Trigger manually to test
launchctl start com.granola.sync

# Check logs immediately
tail -f ~/Library/Logs/granola-sync.log
```

**E. Check LaunchAgent Logs**
```bash
# System log for LaunchAgent errors
log show --predicate 'eventMessage contains "granola"' --last 1h
```

---

### 5. "No module named..." Errors

**Error:**
```
ModuleNotFoundError: No module named 'json'
```

**Causes:**
- Wrong Python version
- Corrupted Python installation

**Solutions:**

**A. Verify Python Version**
```bash
python3 --version
```

Should be 3.7 or later.

**B. Test Standard Library**
```bash
python3 -c "import json; import pathlib; print('OK')"
```

Should print `OK`.

**C. Reinstall Python**
```bash
# If using Homebrew
brew reinstall python3

# Or download from: https://www.python.org/downloads/
```

---

### 6. "Can't make... into type integer" (AppleScript Error)

**Error from clicking Sync Granola.app:**
```
Sync failed: Can't make "Basic" into type integer.
```

**Cause:**
- AppleScript can't parse sync output
- ANSI color codes confusing parser

**Solutions:**

**A. Update AppleScript**
Already fixed in latest version. Recompile:
```bash
osacompile -o ~/Desktop/Sync\ Granola.app src/sync-granola.applescript
```

**B. Test Python Script Directly**
```bash
python3 ~/import-granola-to-memory.py 2>&1 | cat
```

Should show clean output without errors.

**C. Simplify Output Parsing**
Edit `sync-granola.applescript` to not parse counts:
```applescript
-- Just show generic success
set message to "✅ Sync complete"
```

---

### 7. Missing AI-Enhanced Notes

**Symptoms:**
- Only manual notes appear
- Gray text from Granola missing
- Meeting notes say "No notes recorded"

**Solutions:**

**A. Verify Panels Exist in Granola**
1. Open meeting in Granola
2. Check for gray AI-enhanced text
3. Toggle "Enhanced" view

If not visible in Granola, the AI enhancement hasn't run yet.

**B. Check Script Version**
```bash
grep "documentPanels" ~/import-granola-to-memory.py
```

Should appear multiple times. If not, update script:
```bash
cd ~/granola-sync
git pull
cp src/import-granola-to-memory.py ~/
```

**C. Force Re-sync**
```bash
# Re-import all meetings
python3 ~/import-granola-to-memory.py --force
```

---

### 8. Duplicate Files or Wrong Folders

**Symptoms:**
- Meetings in wrong folders
- Multiple copies of same meeting
- Stub files not working

**Solutions:**

**A. Clear Sync State**
```bash
# Delete state file to force clean sync
rm ~/basic-memory/Granola/.granola-sync-state.json

# Re-sync
python3 ~/import-granola-to-memory.py
```

**B. Check Granola Folder Assignments**
1. Open Granola
2. Select meeting
3. View "Folders" field
4. Ensure correct folders assigned

**C. Clean Output Directory**
```bash
# Backup first!
cp -r ~/basic-memory/Granola ~/granola-backup

# Clear (except state)
find ~/basic-memory/Granola -name "*.md" -delete

# Re-sync
python3 ~/import-granola-to-memory.py
```

---

### 9. Slow Sync Performance

**Symptoms:**
- Sync takes 5+ minutes
- High CPU usage
- Disk thrashing

**Solutions:**

**A. Check Incremental Sync**
```bash
# Should say "Last sync: YYYY-MM-DD"
python3 ~/import-granola-to-memory.py | head -10
```

If says "Never", state file missing:
```bash
ls -lh ~/basic-memory/Granola/.granola-sync-state.json
```

**B. Reduce Meeting Count**
Filter old meetings in script:
```python
# Add to main() function
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=180)

for meeting in meetings.values():
    created = meeting.get('created_at', '')
    if created and datetime.fromisoformat(created.replace('Z', '+00:00')) < cutoff:
        continue  # Skip old meetings
```

**C. Disable Transcript Export**
Edit script to skip transcripts:
```python
# Comment out transcript handling
# if transcript_data:
#     export_transcript(...)
```

---

### 10. Notification Not Showing (AppleScript)

**Symptoms:**
- Double-click app, nothing happens
- No success/failure dialog
- Silent execution

**Solutions:**

**A. Check System Notifications**
1. System Preferences → Notifications
2. Find "Script Editor" or app name
3. Enable "Allow Notifications"
4. Set alert style to "Alerts"

**B. Test Notification Manually**
```bash
osascript -e 'display notification "Test" with title "Test Title"'
```

If nothing shows, notifications disabled system-wide.

**C. Run Script in Terminal**
```bash
osascript ~/sync-granola.applescript
```

Will show error messages directly.

---

## Log File Analysis

### View Logs

```bash
# Sync output
cat ~/Library/Logs/granola-sync.log

# Errors only
cat ~/Library/Logs/granola-sync-error.log

# Live monitoring
tail -f ~/Library/Logs/granola-sync.log
```

### Common Log Messages

**Success:**
```
✅ Sync complete!
✨ New meetings: 0
🔄 Updated meetings: 0
```

**Errors:**
```
❌ Granola cache not found
❌ Failed to write: [path]
```

**Warnings:**
```
⚠️ Missing title for meeting: [id]
⚠️ No folder mapping for: [id]
```

---

## Advanced Debugging

### Enable Verbose Output

Edit `import-granola-to-memory.py`:

```python
# Add at top
DEBUG = True

# In functions:
if DEBUG:
    print(f"Processing meeting: {meeting_id}")
    print(f"Folders: {folders}")
    print(f"Updated: {updated_at}")
```

### Inspect Cache Structure

```bash
# Pretty-print cache JSON
python3 -m json.tool ~/Library/Application\ Support/Granola/cache-v3.json | less

# Count meetings
python3 -c "
import json
from pathlib import Path

cache_file = Path.home() / 'Library/Application Support/Granola/cache-v3.json'
with open(cache_file) as f:
    data = json.load(f)
    cache = json.loads(data['cache'])
    meetings = cache['state']['meetings']
    print(f'Total meetings: {len(meetings)}')
"
```

### Test TipTap Parser

```python
# test_parser.py
from pathlib import Path
import json

# Read your script
with open('import-granola-to-memory.py') as f:
    exec(f.read())

# Test with sample data
sample = {
    "type": "doc",
    "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "Test"}]}
    ]
}

result = parse_tiptap_to_markdown(sample)
print(result)
```

---

## Getting Help

If none of these solutions work:

### Collect Diagnostic Info

```bash
# Create diagnostic report
cat > ~/granola-sync-diagnostic.txt << 'EOF'
# System Info
macOS Version: $(sw_vers -productVersion)
Python Version: $(python3 --version)
Granola Cache Size: $(ls -lh ~/Library/Application\ Support/Granola/cache-v3.json 2>&1)

# LaunchAgent Status
$(launchctl list | grep granola)

# Recent Logs
$(tail -20 ~/Library/Logs/granola-sync-error.log 2>&1)

# Permissions
$(ls -ld ~/basic-memory/Granola 2>&1)
EOF

cat ~/granola-sync-diagnostic.txt
```

### Open GitHub Issue

Include:
1. Diagnostic report (above)
2. What you were trying to do
3. Expected behavior
4. Actual behavior
5. Steps to reproduce

---

## Still Having Issues?

1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for how it works
2. Review [SETUP.md](SETUP.md) for correct installation
3. Search existing GitHub issues
4. Open new issue with diagnostics

Remember: Granola Sync only **reads** from Granola's cache. It cannot break or corrupt your Granola data!
