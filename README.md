# Granola Sync

Automatically sync your [Granola](https://www.granola.so/) meeting notes into your local file system with smart incremental updates. Perfect for integrating AI-enhanced meeting notes with knowledge management systems like Obsidian, Basic Memory, or any file-based workflow.

## Features

- **Automatic Daily Sync** - LaunchAgent runs every morning at 9 AM
- **Manual Trigger** - Double-click AppleScript app anytime
- **Smart Incremental Updates** - Only syncs changed meetings
- **Rich Content Preservation** - AI-enhanced notes, transcripts, metadata
- **Folder Structure Mirroring** - Maintains your Granola organization
- **Multi-Folder Support** - Creates stub files for meetings in multiple folders
- **No External Dependencies** - Pure Python standard library
- **Full Transcript Export** - Speaker-attributed conversation logs

## Quick Start

### Prerequisites

- macOS (for LaunchAgent and AppleScript)
- Python 3.x (included with macOS)
- Granola app with local cache

### Three-Step Setup

1. **Clone and configure**
   ```bash
   git clone https://github.com/yourusername/granola-sync.git
   cd granola-sync

   # Edit paths in src/import-granola-to-memory.py if needed
   # Default output: ~/basic-memory/Granola/
   ```

2. **Install the sync script**
   ```bash
   cp src/import-granola-to-memory.py ~/

   # Test it works
   python3 ~/import-granola-to-memory.py
   ```

3. **Set up automation**
   ```bash
   # Manual trigger (creates clickable Desktop app)
   osacompile -o ~/Desktop/Sync\ Granola.app src/sync-granola.applescript

   # Automatic daily sync
   cp config/com.granola.sync.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
   ```

**That's it!** Your Granola meetings are now syncing automatically.

## Usage

### Manual Sync

Double-click "Sync Granola.app" on your Desktop. You'll see:
- Notification when sync starts
- Notification when sync completes
- Count of new/updated meetings

### Automatic Sync

Runs every day at 9:00 AM automatically. Check logs:
```bash
cat ~/Library/Logs/granola-sync.log
```

### Force Full Re-sync

```bash
python3 ~/import-granola-to-memory.py --force
```

## Output Structure

```
~/basic-memory/Granola/
├── _transcripts/              # Full meeting transcripts
├── .granola-sync-state.json   # Sync state (don't delete!)
├── Tax Planning/              # Granola folder
│   └── 2025-11-21_Meeting.md
├── Portfolio (Good)/
│   └── 2025-11-15_Company_Check-in.md
└── [Your Granola Folders]/
    └── [Synced Meetings]/
```

Each meeting note includes:
- Meeting title and date
- Attendee names
- AI-enhanced notes with hierarchical structure
- Private/manual notes
- Link to full transcript (if available)
- Granola app deep link

See [examples/sample-output.md](examples/sample-output.md) for a complete example.

## What Gets Synced

✅ **Included:**
- AI-enhanced notes and summaries
- Manual/private notes
- Meeting metadata (date, people, folders)
- Full transcripts with speaker attribution
- Hierarchical bullet structures
- Rich text formatting (bold, italic, lists, code blocks)

❌ **Not Included:**
- Audio recordings
- Granola app UI preferences
- Comments or collaborative edits

## Configuration

### Change Output Location

Edit `MEMORY_BASE` in `src/import-granola-to-memory.py`:
```python
MEMORY_BASE = Path.home() / "path/to/your/notes"
```

### Change Sync Schedule

Edit `config/com.granola.sync.plist`:
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>21</integer>  <!-- 9 PM instead of 9 AM -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.granola.sync.plist
launchctl load ~/Library/LaunchAgents/com.granola.sync.plist
```

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation and configuration guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive and system design
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[examples/](examples/)** - Sample output files

## How It Works

1. Reads Granola's local cache (`~/Library/Application Support/Granola/cache-v3.json`)
2. Parses TipTap/ProseMirror JSON format into Markdown
3. Tracks sync state to only update changed meetings
4. Preserves folder structure and handles multi-folder assignments
5. Exports to organized directory structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical explanation.

## Utility Scripts

Located in `src/utils/`:

- **extract-granola-full.py** - Full data extraction from cache
- **granola_api.py** - Granola cloud API interaction
- **organize-granola-exports.py** - Organize exported meetings
- **get-granola-meetings.py** - Query meetings by criteria
- **find_meetings_with_notes.py** - Search for meetings with content
- **find_guppshup_meetings.py** - Find specific meeting patterns
- **get_recent_meetings.py** - Get recently updated meetings

## Requirements

- macOS 10.14 or later
- Python 3.7+ (standard library only, no pip packages needed)
- Granola desktop app installed
- ~5 MB disk space per 1000 meetings

## Limitations

- **macOS only** (LaunchAgent and AppleScript are macOS-specific)
- **Local cache required** (must have Granola app installed and signed in)
- **One-way sync** (changes in exported files won't sync back to Granola)

## FAQ

**Q: Can I run this on Windows/Linux?**
A: The core Python script works cross-platform, but the automation (LaunchAgent/AppleScript) is macOS-only. You can use cron or Task Scheduler instead.

**Q: Will this slow down Granola?**
A: No, it only reads from the cache file. Granola won't even notice.

**Q: What if I delete the exported files?**
A: Run with `--force` flag to re-export everything.

**Q: Can I customize the Markdown output?**
A: Yes! Edit the `format_meeting_content()` function in the Python script.

**Q: Does this work with Granola's web app?**
A: It reads from the desktop app's local cache. The web app doesn't create a local cache.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Built for personal use and shared with the community. Granola is a product of Granola Technologies, Inc.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/granola-sync/issues)
- **Granola Support**: [help.granola.so](https://help.granola.so)

---

**Made with ❤️ for better meeting notes organization**
