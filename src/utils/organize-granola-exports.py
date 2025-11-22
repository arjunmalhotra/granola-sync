#!/usr/bin/env python3
"""
Organize Granola exports into your basic-memory structure
"""

import os
import re
from datetime import datetime
from pathlib import Path
import shutil

# Configuration
EXPORTS_DIR = Path.home() / "granola-exports"
BASIC_MEMORY_DIR = Path.home() / "basic-memory"
WORK_MEETINGS_DIR = BASIC_MEMORY_DIR / "areas" / "work" / "meetings"
PERSONAL_MEETINGS_DIR = BASIC_MEMORY_DIR / "areas" / "personal" / "meetings"

def extract_date_from_content(content):
    """Try to extract a date from the note content"""
    # Look for common date patterns
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\w{3},\s+\d{1,2}\s+\w{3}\s+\d{2,4})',  # Thu, 24 Jul 25
        r'(\d{1,2}/\d{1,2}/\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
    ]

    for pattern in date_patterns:
        match = re.search(pattern, content[:500])  # Check first 500 chars
        if match:
            return match.group(1)

    return None

def extract_participants(content):
    """Extract participant names from the content"""
    # Look for common patterns like "with X" or participant lists
    participants = []

    # Look for names after "with" or "and"
    # This is a simple heuristic
    lines = content.split('\n')[:20]  # Check first 20 lines

    for line in lines:
        if any(keyword in line.lower() for keyword in ['participants:', 'attendees:', 'with:', 'meeting with']):
            participants.append(line.strip())

    return participants

def categorize_note(title, content):
    """Determine if note is work or personal"""
    # Check for work-related keywords
    work_keywords = ['investment', 'deal', 'pitch', 'portfolio', 'vc', 'fund',
                     'investopad', 'good capital', 'huddle', 'sync', 'standup']

    title_lower = title.lower()
    content_lower = content[:1000].lower()

    for keyword in work_keywords:
        if keyword in title_lower or keyword in content_lower:
            return 'work'

    return 'personal'

def organize_exports():
    """Main function to organize all exports"""

    if not EXPORTS_DIR.exists():
        print(f"❌ Export directory not found: {EXPORTS_DIR}")
        return

    # Create output directories if they don't exist
    WORK_MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    PERSONAL_MEETINGS_DIR.mkdir(parents=True, exist_ok=True)

    # Get all markdown files
    export_files = list(EXPORTS_DIR.glob("*.md"))

    if not export_files:
        print(f"❌ No markdown files found in {EXPORTS_DIR}")
        return

    print(f"📁 Found {len(export_files)} files to organize")

    work_count = 0
    personal_count = 0
    error_count = 0

    for file_path in export_files:
        try:
            # Read content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract title (first line without # if present)
            lines = content.split('\n')
            title = lines[0].strip()
            if title.startswith('# '):
                title = title[2:].strip()

            # Clean title for filename
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title[:100]  # Limit length

            # Extract date
            date_str = extract_date_from_content(content)
            if not date_str or not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                # Use file modification time as fallback
                timestamp = file_path.stat().st_mtime
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

            # Categorize
            category = categorize_note(title, content)

            # Determine target directory
            if category == 'work':
                target_dir = WORK_MEETINGS_DIR
                work_count += 1
            else:
                target_dir = PERSONAL_MEETINGS_DIR
                personal_count += 1

            # Create new filename
            new_filename = f"{date_str} - {clean_title}.md"
            target_path = target_dir / new_filename

            # Handle duplicates
            counter = 1
            while target_path.exists():
                new_filename = f"{date_str} - {clean_title} ({counter}).md"
                target_path = target_dir / new_filename
                counter += 1

            # Copy file
            shutil.copy2(file_path, target_path)
            print(f"✅ {category.upper()}: {new_filename}")

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            error_count += 1

    print(f"\n📊 Summary:")
    print(f"  Work meetings: {work_count}")
    print(f"  Personal meetings: {personal_count}")
    print(f"  Errors: {error_count}")
    print(f"\n📁 Organized files are in:")
    print(f"  Work: {WORK_MEETINGS_DIR}")
    print(f"  Personal: {PERSONAL_MEETINGS_DIR}")

if __name__ == "__main__":
    organize_exports()
