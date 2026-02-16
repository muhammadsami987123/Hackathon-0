"""
WhatsApp Watcher - Monitors WhatsApp Web for new messages and creates action items.

This watcher uses Playwright to interact with WhatsApp Web.
Note: Be aware of WhatsApp's terms of service regarding automated access.

Usage:
    python whatsapp_watcher.py [--vault-path /path/to/vault] [--session-path /path/to/session]
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """Watches WhatsApp Web for new messages and creates action items."""

    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 60, headless: bool = True):
        super().__init__(vault_path, check_interval)
        self.session_path = Path(session_path) if session_path else self.vault_path / "whatsapp_session"
        self.headless = headless
        self.processed_messages = set()
        self.keywords = [
            'urgent', 'asap', 'help', 'invoice', 'payment', 'money',
            'project', 'deadline', 'meeting', 'important'
        ]

    def _setup_page(self):
        """Set up the Playwright browser and WhatsApp Web page."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=self.headless,
                viewport={'width': 1280, 'height': 800}
            )
            self.page = self.browser.new_page()
            self.page.goto('https://web.whatsapp.com')
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup WhatsApp session: {e}")
            return False

    def check_for_updates(self) -> list:
        """Check for new WhatsApp messages."""
        messages = []

        try:
            # Wait for WhatsApp Web to load
            if not self.page.is_visible('[data-testid="chat-list"]'):
                self.logger.info("WhatsApp Web not loaded, waiting...")
                if not self.page.wait_for_selector('[data-testid="chat-list"]', timeout=10000):
                    self.logger.error("WhatsApp Web took too long to load")
                    return []

            # Find unread chats
            unread_chats = self.page.query_selector_all('[data-testid="default-list-item-unread"]')

            for chat in unread_chats:
                # Click on the chat
                chat.click()
                time.sleep(1)  # Wait for messages to load

                # Get the last few messages in the chat
                message_bubbles = self.page.query_selector_all('[data-testid="conversation-turn"]')

                for bubble in message_bubbles[-3:]:  # Check last 3 messages
                    message_text = bubble.inner_text()

                    # Create a unique ID based on message content and sender
                    sender = chat.get_attribute('title') or "Unknown"
                    message_id = f"{sender}_{hash(message_text)}_{int(time.time())}"

                    if message_id not in self.processed_messages:
                        # Check if message contains high-priority keywords
                        priority = 'high' if any(kw in message_text.lower() for kw in self.keywords) else 'medium'

                        # Check if this is a new message (not from self)
                        if not self.page.query_selector('[data-testid="sent-message-container"]', timeout=1000):
                            # This is a received message
                            message_data = {
                                'id': message_id,
                                'sender': sender,
                                'content': message_text,
                                'timestamp': datetime.now().isoformat(),
                                'priority': priority,
                                'chat_name': chat.get_attribute('title')
                            }
                            messages.append(message_data)
                            self.processed_messages.add(message_id)

        except Exception as e:
            self.logger.error(f"Error checking WhatsApp messages: {e}")

        return messages

    def create_action_file(self, message_data) -> Path:
        """Create an action file for a WhatsApp message."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize sender name for filename
        sender_sanitized = message_data['sender'].replace('@', '_at_').replace('.', '_').replace(' ', '_')

        content = f"""---
type: whatsapp_message
from: {message_data['sender']}
chat: {message_data['chat_name']}
received: {message_data['timestamp']}
priority: {message_data['priority']}
status: pending
---

## WhatsApp Message

{message_data['content']}

## Sender Information
- Contact: {message_data['sender']}
- Chat: {message_data['chat_name']}
- Received: {message_data['timestamp']}

## Suggested Actions
- [ ] Review message content
- [ ] Check Company Handbook for response guidelines
- [ ] Respond to message (REQUIRES APPROVAL for new contacts)
- [ ] Flag important topics for follow-up
- [ ] Update contact information if new client/inquiry

## Compliance Check
- [ ] Verify sender is in approved contacts list
- [ ] Ensure response follows Company_Handbook.md guidelines
- [ ] Flag for human review if sensitive topic
- [ ] Check if response contains confidential information
"""

        # Create filename
        filename = f"WHATSAPP_{timestamp}_{sender_sanitized}.md"
        filepath = self.needs_action / filename

        # Write the content
        filepath.write_text(content)

        # Log the action
        self.log_action(
            "whatsapp_message_processed",
            {
                "message_id": message_data['id'],
                "sender": message_data['sender'],
                "content_preview": message_data['content'][:100],
                "file_created": str(filepath),
                "priority": message_data['priority']
            }
        )

        return filepath

    def run(self):
        """Main loop with browser setup."""
        # Setup browser and WhatsApp session
        if not self._setup_page():
            self.logger.error("Could not initialize WhatsApp watcher")
            return

        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("WhatsApp Web watcher is running. Keep this window open.")

        try:
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
                    self.logger.info("WhatsApp watcher stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in WhatsApp watcher loop: {e}")
                    self.log_action("error", {"error": str(e)})

                # Wait before next check
                time.sleep(self.check_interval)
        finally:
            # Clean up
            self.browser.close()
            self.playwright.stop()


def main():
    parser = argparse.ArgumentParser(description="AI Employee WhatsApp Watcher")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the Obsidian vault (default: parent of scripts/)",
    )
    parser.add_argument(
        "--session-path",
        help="Path to WhatsApp session directory (for persistent login)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in headful mode (visible)",
    )
    args = parser.parse_args()

    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        session_path=args.session_path,
        check_interval=args.interval,
        headless=not args.no_headless
    )
    watcher.run()


if __name__ == "__main__":
    main()