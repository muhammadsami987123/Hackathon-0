"""
Orchestrator - Master process for the AI Employee.

Responsibilities:
1. Watch /Needs_Action for new items to process
2. Trigger Claude Code to reason about and handle items
3. Manage the workflow: Needs_Action → In_Progress → Done
4. Watch /Approved for approved actions to execute
5. Maintain system health and logging

Usage:
    python orchestrator.py [--vault-path /path/to/vault] [--dry-run] [--interval 30]
"""

import argparse
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path


class Orchestrator:
    """Master process that coordinates the AI Employee workflow."""

    def __init__(self, vault_path: str, check_interval: int = 30, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval
        self.dry_run = dry_run

        # Core directories
        self.needs_action = self.vault_path / "Needs_Action"
        self.in_progress = self.vault_path / "In_Progress"
        self.done = self.vault_path / "Done"
        self.plans = self.vault_path / "Plans"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.approved = self.vault_path / "Approved"
        self.rejected = self.vault_path / "Rejected"
        self.logs_dir = self.vault_path / "Logs"

        # Ensure all directories exist
        for d in [
            self.needs_action, self.in_progress, self.done,
            self.plans, self.pending_approval, self.approved,
            self.rejected, self.logs_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger("Orchestrator")
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.logs_dir / "orchestrator.log"),
                logging.StreamHandler(),
            ],
        )

    def log_action(self, action_type: str, details: dict):
        """Append to the daily JSON log."""
        log_file = self.logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                entries = []

        entries.append({
            "timestamp": datetime.now().isoformat(),
            "actor": "orchestrator",
            "action_type": action_type,
            "details": details,
        })
        log_file.write_text(json.dumps(entries, indent=2))

    def get_pending_items(self) -> list[Path]:
        """Get all .md files in /Needs_Action."""
        if not self.needs_action.exists():
            return []
        return sorted(self.needs_action.glob("*.md"), key=lambda p: p.stat().st_mtime)

    def get_approved_items(self) -> list[Path]:
        """Get all .md files in /Approved."""
        if not self.approved.exists():
            return []
        return sorted(self.approved.glob("*.md"), key=lambda p: p.stat().st_mtime)

    def claim_item(self, item: Path) -> Path | None:
        """Move item from Needs_Action to In_Progress (claim-by-move)."""
        dest = self.in_progress / item.name
        if dest.exists():
            self.logger.warning(f"Item already in progress: {item.name}")
            return None

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would claim: {item.name}")
            return dest

        item.rename(dest)
        self.log_action("item_claimed", {"item": item.name, "destination": str(dest)})
        return dest

    def complete_item(self, item: Path):
        """Move item from In_Progress to Done."""
        dest = self.done / item.name
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would complete: {item.name}")
            return

        item.rename(dest)
        self.log_action("item_completed", {"item": item.name})

    def process_item(self, item: Path):
        """Process a single action item using Claude Code."""
        self.logger.info(f"Processing: {item.name}")

        # Read the item content
        content = item.read_text()

        # Create a plan for Claude to execute
        plan_content = f"""---
created: {datetime.now().isoformat()}
source: {item.name}
status: in_progress
---

## Task: Process {item.name}

### Source Content
{content}

### Instructions
1. Read the Company_Handbook.md for applicable rules
2. Determine the appropriate action based on item type
3. Execute auto-approved actions
4. Create approval requests for sensitive actions in /Pending_Approval
5. Update Dashboard.md with activity
6. Move completed items to /Done
"""
        plan_path = self.plans / f"PLAN_{item.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create plan: {plan_path.name}")
            return

        plan_path.write_text(plan_content)
        self.log_action("plan_created", {"plan": str(plan_path), "source": item.name})

        # Trigger Claude Code to process the plan
        self.trigger_claude(plan_path)

    def trigger_claude(self, plan_path: Path):
        """Trigger Claude Code to process a plan file."""
        prompt = (
            f"Read the file at {plan_path} and execute the plan. "
            f"Follow the rules in Company_Handbook.md at {self.vault_path / 'Company_Handbook.md'}. "
            f"Update Dashboard.md when done."
        )

        self.logger.info(f"Triggering Claude Code for: {plan_path.name}")

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would invoke Claude with prompt: {prompt[:100]}...")
            return

        try:
            result = subprocess.run(
                ["claude", "--print", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.vault_path),
            )
            if result.returncode == 0:
                self.logger.info(f"Claude processed: {plan_path.name}")
                self.log_action("claude_invoked", {
                    "plan": str(plan_path),
                    "result": "success",
                    "output_preview": result.stdout[:200] if result.stdout else "",
                })
            else:
                self.logger.error(f"Claude error: {result.stderr[:200]}")
                self.log_action("claude_error", {
                    "plan": str(plan_path),
                    "error": result.stderr[:200] if result.stderr else "unknown",
                })
        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude timed out processing: {plan_path.name}")
            self.log_action("claude_timeout", {"plan": str(plan_path)})
        except FileNotFoundError:
            self.logger.error("Claude Code not found. Ensure 'claude' is in PATH.")
            self.log_action("claude_not_found", {})

    def process_approved(self, item: Path):
        """Process an approved action."""
        self.logger.info(f"Processing approved action: {item.name}")
        content = item.read_text()

        self.log_action("approved_action_processing", {"item": item.name})

        # Trigger Claude to execute the approved action
        self.trigger_claude(item)

        # Move to Done
        self.complete_item(item)

    def update_dashboard_status(self, status: str):
        """Update the system status section of Dashboard.md."""
        dashboard = self.vault_path / "Dashboard.md"
        if not dashboard.exists():
            return

        content = dashboard.read_text()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Update orchestrator status line
        old_line = "| Orchestrator | "
        if old_line in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if old_line in line:
                    lines[i] = f"| Orchestrator | {status} | {now} |"
                    break
            dashboard.write_text("\n".join(lines))

    def run(self):
        """Main orchestration loop."""
        self.logger.info("=" * 60)
        self.logger.info("AI Employee Orchestrator Starting")
        self.logger.info(f"Vault: {self.vault_path}")
        self.logger.info(f"Interval: {self.check_interval}s")
        self.logger.info(f"Dry run: {self.dry_run}")
        self.logger.info("=" * 60)

        self.update_dashboard_status("✅ Running")
        self.log_action("orchestrator_started", {"vault": str(self.vault_path)})

        try:
            while True:
                # 1. Process items in Needs_Action
                pending = self.get_pending_items()
                if pending:
                    self.logger.info(f"Found {len(pending)} pending items")
                for item in pending:
                    claimed = self.claim_item(item)
                    if claimed:
                        self.process_item(claimed)

                # 2. Process approved actions
                approved = self.get_approved_items()
                if approved:
                    self.logger.info(f"Found {len(approved)} approved actions")
                for item in approved:
                    self.process_approved(item)

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info("Orchestrator stopped by user")
            self.update_dashboard_status("🔴 Offline")
            self.log_action("orchestrator_stopped", {"reason": "user_interrupt"})


def main():
    parser = argparse.ArgumentParser(description="AI Employee Orchestrator")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the Obsidian vault",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log actions without executing them",
    )
    args = parser.parse_args()

    orchestrator = Orchestrator(
        vault_path=args.vault_path,
        check_interval=args.interval,
        dry_run=args.dry_run,
    )
    orchestrator.run()


if __name__ == "__main__":
    main()
