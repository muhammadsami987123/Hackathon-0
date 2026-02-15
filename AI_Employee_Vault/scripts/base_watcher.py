"""
Base Watcher - Template for all AI Employee watchers.

All watchers follow the Perception layer pattern:
  Monitor external source → Detect changes → Create .md action files in /Needs_Action
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    """Abstract base class for all watcher scripts."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.logs_dir = self.vault_path / "Logs"
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure required directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.logs_dir / f"{self.__class__.__name__}.log"),
                logging.StreamHandler(),
            ],
        )

    @abstractmethod
    def check_for_updates(self) -> list:
        """Return list of new items to process."""
        pass

    @abstractmethod
    def create_action_file(self, item) -> Path:
        """Create .md file in Needs_Action folder."""
        pass

    def log_action(self, action_type: str, details: dict):
        """Log an action to the daily log file."""
        import json

        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

        entry = {
            "timestamp": datetime.now().isoformat(),
            "watcher": self.__class__.__name__,
            "action_type": action_type,
            "details": details,
        }

        # Append to daily log
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                entries = []

        entries.append(entry)
        log_file.write_text(json.dumps(entries, indent=2))

    def run(self):
        """Main loop - continuously check for updates."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")

        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    filepath = self.create_action_file(item)
                    self.logger.info(f"Created action file: {filepath}")
                    self.log_action(
                        "action_file_created",
                        {"file": str(filepath)},
                    )
            except KeyboardInterrupt:
                self.logger.info("Watcher stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in watcher loop: {e}")
                self.log_action("error", {"error": str(e)})
            time.sleep(self.check_interval)
