"""
Gmail Watcher - Monitors Gmail for new messages and creates action items.

Usage:
    python gmail_watcher.py [--vault-path /path/to/vault] [--credentials /path/to/creds.json]
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher


class GmailWatcher(BaseWatcher):
    """Watches Gmail inbox for new messages and creates action items."""

    # Scopes required for reading Gmail
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, vault_path: str, credentials_path: str = None,
                 check_interval: int = 300):  # 5 minutes
        super().__init__(vault_path, check_interval)
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.processed_ids = set()
        self.service = self._setup_gmail_service()

    def _setup_gmail_service(self):
        """Set up Gmail API service."""
        creds = None

        # Token file stores the user's access and refresh tokens
        token_path = self.vault_path / "token.json"

        # Load existing token if available
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    # If refresh fails, remove token and re-authenticate
                    if token_path.exists():
                        token_path.unlink()
                    creds = None

            if not creds:
                if not self.credentials_path or not self.credentials_path.exists():
                    print("Credentials file not found. Gmail watcher will not function.")
                    return None
                else:
                    # Run OAuth flow (in non-interactive mode for this implementation)
                    print("OAuth flow required. Please set up credentials following Google's guide.")
                    return None

            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        if creds:
            return build('gmail', 'v1', credentials=creds)
        else:
            print("Could not set up Gmail service. Gmail watcher will not function.")
            return None

    def check_for_updates(self) -> list:
        """Check for new messages in Gmail."""
        if not self.service:
            return []

        try:
            # Get messages from the past 24 hours
            query = "after:1d"
            results = self.service.users().messages().list(
                userId="me",
                q=query
            ).execute()

            messages = results.get("messages", [])
            new_messages = []

            for message in messages:
                if message['id'] not in self.processed_ids:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId="me",
                        id=message['id']
                    ).execute()
                    new_messages.append(msg)
                    self.processed_ids.add(message['id'])

            return new_messages

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def create_action_file(self, message) -> Path:
        """Create an action file for a Gmail message."""
        # Extract headers
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}

        # Extract subject and sender
        subject = headers.get('Subject', 'No Subject')
        sender = headers.get('From', 'Unknown Sender')

        # Extract snippet (preview text)
        snippet = message.get('snippet', 'No content available')

        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Determine message priority based on subject keywords
        high_priority_keywords = ['urgent', 'asap', 'help', 'payment', 'invoice', 'immediate']
        priority = 'high' if any(keyword in subject.lower() for keyword in high_priority_keywords) else 'medium'

        # Create action file content
        content = f"""---
type: email
from: {sender}
subject: {subject}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

## Email Content

{snippet}

## Headers
- From: {headers.get('From', 'Unknown')}
- To: {headers.get('To', 'Unknown')}
- Date: {headers.get('Date', 'Unknown')}
- Subject: {subject}

## Suggested Actions
- [ ] Read full message
- [ ] Review Company Handbook for response guidelines
- [ ] Reply to sender (REQUIRES APPROVAL if new contact)
- [ ] Forward to relevant party (if applicable)
- [ ] Archive after processing (if no further action needed)

## Compliance Check
- [ ] Verify sender is in approved contacts list
- [ ] Ensure response follows Company_Handbook.md guidelines
- [ ] Flag for human review if sensitive topic
"""

        # Create filename
        filename = f"EMAIL_{timestamp}_{headers.get('From', 'unknown').replace('@', '_at_').replace('.', '_')}.md"
        filepath = self.needs_action / filename

        # Write the content
        filepath.write_text(content)

        # Log the action
        self.log_action(
            "gmail_message_processed",
            {
                "message_id": message['id'],
                "subject": subject,
                "sender": sender,
                "file_created": str(filepath),
                "priority": priority
            }
        )

        return filepath


def main():
    parser = argparse.ArgumentParser(description="AI Employee Gmail Watcher")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the Obsidian vault (default: parent of scripts/)",
    )
    parser.add_argument(
        "--credentials",
        help="Path to the Gmail credentials JSON file",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)",
    )
    args = parser.parse_args()

    watcher = GmailWatcher(
        vault_path=args.vault_path,
        credentials_path=args.credentials,
        check_interval=args.interval
    )
    watcher.run()


if __name__ == "__main__":
    main()