"""
LinkedIn Watcher - Monitors LinkedIn for new messages, connection requests, and activity.

This watcher uses Playwright to interact with LinkedIn.
Note: Be aware of LinkedIn's terms of service regarding automated access.

Usage:
    python linkedin_watcher.py [--vault-path /path/to/vault] [--session-path /path/to/session]
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """Watches LinkedIn for new messages, connection requests, and posts, creating action items."""

    def __init__(self, vault_path: str, session_path: str = None,
                 check_interval: int = 600, headless: bool = True):
        super().__init__(vault_path, check_interval)
        self.session_path = Path(session_path) if session_path else self.vault_path / "linkedin_session"
        self.headless = headless
        self.processed_items = set()
        self.keywords = [
            'opportunity', 'project', 'consulting', 'freelance', 'hire', 'work',
            'urgent', 'asap', 'important', 'proposal', 'bid', 'contract'
        ]

    def _setup_page(self):
        """Set up the Playwright browser and LinkedIn page."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch_persistent_context(
                str(self.session_path),
                headless=self.headless,
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.page = self.browser.new_page()
            self.page.goto('https://www.linkedin.com')
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup LinkedIn session: {e}")
            return False

    def check_for_updates(self) -> list:
        """Check for new LinkedIn activity."""
        items = []

        try:
            # Wait for LinkedIn to load
            if not self.page.is_visible('main'):
                self.logger.info("LinkedIn not loaded, waiting...")
                if not self.page.wait_for_selector('main', timeout=10000):
                    self.logger.error("LinkedIn took too long to load")
                    return []

            # Navigate to messages section
            self.page.goto('https://www.linkedin.com/messaging/')
            time.sleep(2)

            # Find unread messages
            unread_messages = self.page.query_selector_all('[data-test-is-read="false"]')

            for msg_element in unread_messages:
                try:
                    # Get message details
                    sender_element = msg_element.query_selector('[data-test-send-message-to-recipient]')
                    if sender_element:
                        sender = sender_element.get_attribute('data-test-send-message-to-recipient')
                    else:
                        sender = "Unknown"

                    # Get conversation preview
                    preview_element = msg_element.query_selector('.msg-thread__snippet-text')
                    if preview_element:
                        preview = preview_element.inner_text()
                    else:
                        preview = "No preview available"

                    # Create a unique ID based on message content and sender
                    message_id = f"linkedin_msg_{hash(preview)}_{int(time.time())}"

                    if message_id not in self.processed_items:
                        # Check priority based on keywords
                        priority = 'high' if any(kw in preview.lower() for kw in self.keywords) else 'medium'

                        item_data = {
                            'id': message_id,
                            'type': 'message',
                            'from': sender,
                            'content': preview,
                            'timestamp': datetime.now().isoformat(),
                            'priority': priority
                        }
                        items.append(item_data)
                        self.processed_items.add(message_id)
                except Exception as e:
                    self.logger.debug(f"Error processing message element: {e}")
                    continue

            # Also check for connection requests
            self.page.goto('https://www.linkedin.com/mynetwork/')
            time.sleep(2)

            connection_requests = self.page.query_selector_all('[data-control-name="accept"]')

            for req_element in connection_requests:
                try:
                    # Get sender info
                    sender_element = req_element.query_selector('img')
                    if sender_element:
                        sender = sender_element.get_attribute('alt') or "Unknown Connection Request"
                    else:
                        sender = "Unknown Connection Request"

                    # Create a unique ID
                    req_id = f"linkedin_conn_{hash(sender)}_{int(time.time())}"

                    if req_id not in self.processed_items:
                        item_data = {
                            'id': req_id,
                            'type': 'connection_request',
                            'from': sender,
                            'content': f"New connection request from {sender}",
                            'timestamp': datetime.now().isoformat(),
                            'priority': 'medium'
                        }
                        items.append(item_data)
                        self.processed_items.add(req_id)
                except Exception as e:
                    self.logger.debug(f"Error processing connection request: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")

        return items

    def create_action_file(self, item_data) -> Path:
        """Create an action file for a LinkedIn item."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Sanitize sender name for filename
        sender_sanitized = item_data['from'].replace(' ', '_').replace('@', '_at_').replace('.', '_')

        if item_data['type'] == 'connection_request':
            content = f"""---
type: linkedin_connection
from: {item_data['from']}
item_type: connection_request
received: {item_data['timestamp']}
priority: {item_data['priority']}
status: pending
---

## LinkedIn Connection Request

{item_data['content']}

## Sender Information
- Contact: {item_data['from']}
- Type: Connection Request
- Received: {item_data['timestamp']}

## Suggested Actions
- [ ] Review sender's profile for legitimacy
- [ ] Check Company Handbook for connection guidelines
- [ ] Accept or decline connection (REQUIRES APPROVAL)
- [ ] Add to CRM if business connection
- [ ] Send welcome message if accepted

## Compliance Check
- [ ] Verify sender is not a competitor
- [ ] Ensure connection follows Company_Handbook.md guidelines
- [ ] Flag for human review if unsure
"""
        else:
            content = f"""---
type: linkedin_message
from: {item_data['from']}
item_type: message
received: {item_data['timestamp']}
priority: {item_data['priority']}
status: pending
---

## LinkedIn Message

{item_data['content']}

## Sender Information
- Contact: {item_data['from']}
- Type: Direct Message
- Received: {item_data['timestamp']}

## Suggested Actions
- [ ] Review message content
- [ ] Check Company Handbook for response guidelines
- [ ] Respond to message (REQUIRES APPROVAL)
- [ ] Flag important opportunities for follow-up
- [ ] Update CRM if applicable

## Compliance Check
- [ ] Verify sender is in approved contacts list
- [ ] Ensure response follows Company_Handbook.md guidelines
- [ ] Flag for human review if sensitive topic
- [ ] Check if response contains confidential information
"""

        # Create filename
        file_type = "CONNECTION" if item_data['type'] == 'connection_request' else "MESSAGE"
        filename = f"LINKEDIN_{file_type}_{timestamp}_{sender_sanitized}.md"
        filepath = self.needs_action / filename

        # Write the content
        filepath.write_text(content)

        # Log the action
        self.log_action(
            "linkedin_item_processed",
            {
                "item_id": item_data['id'],
                "sender": item_data['from'],
                "content_preview": item_data['content'][:100],
                "file_created": str(filepath),
                "item_type": item_data['type']
            }
        )

        return filepath

    def run(self):
        """Main loop with browser setup."""
        # Setup browser and LinkedIn session
        if not self._setup_page():
            self.logger.error("Could not initialize LinkedIn watcher")
            return

        self.logger.info(f"Starting {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval}s")
        self.logger.info("LinkedIn watcher is running. Keep this window open.")

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
                    self.logger.info("LinkedIn watcher stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in LinkedIn watcher loop: {e}")
                    self.log_action("error", {"error": str(e)})

                # Wait before next check
                time.sleep(self.check_interval)
        finally:
            # Clean up
            self.browser.close()
            self.playwright.stop()


def main():
    parser = argparse.ArgumentParser(description="AI Employee LinkedIn Watcher")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the Obsidian vault (default: parent of scripts/)",
    )
    parser.add_argument(
        "--session-path",
        help="Path to LinkedIn session directory (for persistent login)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=600,  # 10 minutes
        help="Check interval in seconds (default: 600)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in headful mode (visible)",
    )
    args = parser.parse_args()

    watcher = LinkedInWatcher(
        vault_path=args.vault_path,
        session_path=args.session_path,
        check_interval=args.interval,
        headless=not args.no_headless
    )
    watcher.run()


if __name__ == "__main__":
    main()