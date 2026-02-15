"""
File System Watcher - Monitors a drop folder for new files.

When files are dropped into the /Inbox folder, this watcher:
1. Detects the new file
2. Copies it to /Needs_Action with a FILE_ prefix
3. Creates a metadata .md file for Claude to process

Usage:
    python filesystem_watcher.py [--vault-path /path/to/vault] [--dry-run]
"""

import argparse
import shutil
import os
from pathlib import Path
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import sys
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler):
    """Handles file system events in the Inbox/drop folder."""

    def __init__(self, watcher: "FileSystemWatcher"):
        self.watcher = watcher

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)

        # Ignore hidden files and temp files
        if source.name.startswith(".") or source.name.startswith("~"):
            return

        self.watcher.logger.info(f"New file detected: {source.name}")
        self.watcher.process_file(source)


class FileSystemWatcher(BaseWatcher):
    """Watches the /Inbox folder for new files and creates action items."""

    def __init__(self, vault_path: str, dry_run: bool = False):
        super().__init__(vault_path, check_interval=5)
        self.inbox = self.vault_path / "Inbox"
        self.inbox.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        self.observer = None
        self.processed_files: set[str] = set()

    def check_for_updates(self) -> list:
        """Check for any existing files in Inbox that haven't been processed."""
        new_files = []
        if self.inbox.exists():
            for filepath in self.inbox.iterdir():
                if filepath.is_file() and str(filepath) not in self.processed_files:
                    if not filepath.name.startswith(".") and not filepath.name.startswith("~"):
                        new_files.append(filepath)
        return new_files

    def create_action_file(self, item) -> Path:
        """Create action file from a detected file."""
        return self.process_file(item)

    def process_file(self, source: Path) -> Path:
        """Process a new file: copy to Needs_Action and create metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"FILE_{timestamp}_{source.name}"

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would process: {source.name} -> {dest_name}")
            self.processed_files.add(str(source))
            return self.needs_action / dest_name

        # Copy file to Needs_Action
        dest = self.needs_action / dest_name
        shutil.copy2(source, dest)

        # Create metadata markdown file
        meta_content = f"""---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
extension: {source.suffix}
detected_at: {datetime.now().isoformat()}
source_path: {source}
status: pending
priority: medium
---

## New File Dropped for Processing

**File:** {source.name}
**Size:** {source.stat().st_size} bytes
**Type:** {source.suffix or 'unknown'}
**Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Suggested Actions
- [ ] Review file contents
- [ ] Categorize file type
- [ ] Process according to Company Handbook rules
- [ ] Move to appropriate project folder
- [ ] Update Dashboard.md
"""
        meta_path = self.needs_action / f"FILE_{timestamp}_{source.stem}.md"
        meta_path.write_text(meta_content)

        self.processed_files.add(str(source))

        self.log_action(
            "file_processed",
            {
                "original": source.name,
                "destination": str(dest),
                "metadata": str(meta_path),
                "size": source.stat().st_size,
            },
        )

        return meta_path

    def run(self):
        """Run the file system watcher using watchdog for real-time detection."""
        self.logger.info(f"Starting FileSystem Watcher")
        self.logger.info(f"Watching: {self.inbox}")
        self.logger.info(f"Dry run: {self.dry_run}")

        # First, process any existing files in Inbox
        existing = self.check_for_updates()
        for item in existing:
            self.process_file(item)
            self.logger.info(f"Processed existing file: {item.name}")

        # Set up real-time monitoring
        handler = DropFolderHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.inbox), recursive=False)
        self.observer.start()

        self.logger.info("File system watcher is running. Press Ctrl+C to stop.")

        try:
            while True:
                self.observer.join(timeout=1)
        except KeyboardInterrupt:
            self.logger.info("Stopping file system watcher...")
            self.observer.stop()
        self.observer.join()


def main():
    parser = argparse.ArgumentParser(description="AI Employee File System Watcher")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the Obsidian vault (default: parent of scripts/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing them",
    )
    args = parser.parse_args()

    watcher = FileSystemWatcher(args.vault_path, dry_run=args.dry_run)
    watcher.run()


if __name__ == "__main__":
    main()
