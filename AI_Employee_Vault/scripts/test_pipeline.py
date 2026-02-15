"""
Integration Test - Tests the full AI Employee pipeline end-to-end.

Tests:
1. FileSystem Watcher detects a file dropped in /Inbox
2. Action file is created in /Needs_Action
3. Orchestrator claims the item (moves to /In_Progress)
4. Orchestrator creates a Plan
5. Item is logged properly
6. Dashboard status is updated

Usage:
    python test_pipeline.py
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Fix imports
sys.path.insert(0, str(Path(__file__).parent))

VAULT = Path(__file__).parent.parent
PASS = "PASS"
FAIL = "FAIL"
results = []


def log_result(test_name: str, status: str, detail: str = ""):
    results.append((test_name, status, detail))
    icon = "[OK]" if status == PASS else "[FAIL]"
    print(f"  {icon} {test_name}: {status} {detail}")


def test_vault_structure():
    """Test 1: Verify all required vault folders exist."""
    print("\n=== Test 1: Vault Structure ===")
    required_folders = [
        "Inbox", "Needs_Action", "In_Progress", "Done",
        "Plans", "Pending_Approval", "Approved", "Rejected",
        "Logs", "Accounting", "Briefings", "Invoices",
        "Active_Project", "Updates",
    ]
    for folder in required_folders:
        path = VAULT / folder
        if path.exists() and path.is_dir():
            log_result(f"Folder /{folder}", PASS)
        else:
            log_result(f"Folder /{folder}", FAIL, f"Not found at {path}")


def test_core_files():
    """Test 2: Verify core markdown files exist and have content."""
    print("\n=== Test 2: Core Files ===")
    required_files = {
        "Dashboard.md": ["System Status", "Financial Summary", "Recent Activity"],
        "Company_Handbook.md": ["Communication Policies", "Financial Rules", "Action Boundaries"],
        "Business_Goals.md": ["Revenue Target", "Key Metrics", "Subscription Audit"],
    }
    for filename, expected_sections in required_files.items():
        path = VAULT / filename
        if not path.exists():
            log_result(f"File {filename}", FAIL, "Not found")
            continue

        content = path.read_text()
        if len(content) < 100:
            log_result(f"File {filename}", FAIL, "Too short / empty")
            continue

        missing = [s for s in expected_sections if s not in content]
        if missing:
            log_result(f"File {filename}", FAIL, f"Missing sections: {missing}")
        else:
            log_result(f"File {filename}", PASS, f"{len(content)} bytes, all sections present")


def test_filesystem_watcher():
    """Test 3: Drop a file in /Inbox and verify watcher creates action file."""
    print("\n=== Test 3: FileSystem Watcher ===")

    from filesystem_watcher import FileSystemWatcher

    watcher = FileSystemWatcher(str(VAULT), dry_run=False)

    # Create a test file in Inbox
    test_file = VAULT / "Inbox" / "test_invoice_client_x.txt"
    test_file.write_text("Please send invoice for February 2026 - $2,500")
    log_result("Test file created in /Inbox", PASS, test_file.name)

    # Manually trigger the watcher check (instead of running the loop)
    items = watcher.check_for_updates()
    if not items:
        log_result("Watcher detected file", FAIL, "No items found")
        return

    log_result("Watcher detected file", PASS, f"Found {len(items)} item(s)")

    # Process the file
    for item in items:
        result_path = watcher.create_action_file(item)
        if result_path and result_path.parent == VAULT / "Needs_Action":
            log_result("Action file created in /Needs_Action", PASS, result_path.name)
        else:
            log_result("Action file created in /Needs_Action", FAIL, str(result_path))

    # Verify the action file exists
    action_files = list((VAULT / "Needs_Action").glob("FILE_*.md"))
    if action_files:
        content = action_files[0].read_text()
        if "type: file_drop" in content and "test_invoice_client_x" in content:
            log_result("Action file has correct metadata", PASS)
        else:
            log_result("Action file has correct metadata", FAIL, "Missing expected content")
    else:
        log_result("Action file has correct metadata", FAIL, "No .md files in Needs_Action")

    # Verify the raw file was also copied
    copied_files = list((VAULT / "Needs_Action").glob("FILE_*test_invoice*"))
    if copied_files:
        log_result("Raw file copied to /Needs_Action", PASS)
    else:
        log_result("Raw file copied to /Needs_Action", FAIL)


def test_orchestrator():
    """Test 4: Orchestrator claims items and creates plans."""
    print("\n=== Test 4: Orchestrator ===")

    from orchestrator import Orchestrator

    orch = Orchestrator(str(VAULT), check_interval=5, dry_run=True)

    # Check for pending items
    pending = orch.get_pending_items()
    if pending:
        log_result("Orchestrator found pending items", PASS, f"{len(pending)} item(s)")
    else:
        log_result("Orchestrator found pending items", FAIL, "No items in /Needs_Action")
        return

    # Test claim-by-move (dry run)
    item = pending[0]
    claimed = orch.claim_item(item)
    if claimed:
        log_result("Claim-by-move (dry run)", PASS, f"Would move to {claimed.name}")
    else:
        log_result("Claim-by-move (dry run)", FAIL)

    # Now test real claim
    orch_real = Orchestrator(str(VAULT), check_interval=5, dry_run=False)
    pending = orch_real.get_pending_items()
    if pending:
        item = pending[0]
        claimed = orch_real.claim_item(item)
        if claimed and claimed.exists():
            log_result("Claim-by-move (real)", PASS, f"Moved to /In_Progress/{claimed.name}")
        else:
            log_result("Claim-by-move (real)", FAIL, "File not moved")

        # Test plan creation
        orch_real.process_item(claimed)
        plans = list((VAULT / "Plans").glob("PLAN_*.md"))
        if plans:
            plan_content = plans[-1].read_text()
            if "status: in_progress" in plan_content:
                log_result("Plan created", PASS, plans[-1].name)
            else:
                log_result("Plan created", FAIL, "Missing expected content")
        else:
            log_result("Plan created", FAIL, "No plans in /Plans")

        # Move claimed item to Done
        orch_real.complete_item(claimed)
        done_files = list((VAULT / "Done").glob("*.md"))
        if done_files:
            log_result("Item moved to /Done", PASS, done_files[-1].name)
        else:
            log_result("Item moved to /Done", FAIL)


def test_logging():
    """Test 5: Verify audit logging is working."""
    print("\n=== Test 5: Audit Logging ===")

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = VAULT / "Logs" / f"{today}.json"

    if not log_file.exists():
        log_result("Daily log file exists", FAIL, f"Expected {log_file.name}")
        return

    try:
        entries = json.loads(log_file.read_text())
        if isinstance(entries, list) and len(entries) > 0:
            log_result("Daily log file exists", PASS, f"{len(entries)} entries")
        else:
            log_result("Daily log file exists", FAIL, "Empty or invalid")
    except json.JSONDecodeError as e:
        log_result("Daily log file exists", FAIL, f"Invalid JSON: {e}")
        return

    # Check log entry structure
    entry = entries[0]
    required_keys = ["timestamp", "action_type"]
    missing = [k for k in required_keys if k not in entry]
    if missing:
        log_result("Log entry structure", FAIL, f"Missing keys: {missing}")
    else:
        log_result("Log entry structure", PASS, f"Keys: {list(entry.keys())}")

    # Check watcher log
    watcher_log = VAULT / "Logs" / "FileSystemWatcher.log"
    if watcher_log.exists() and watcher_log.stat().st_size > 0:
        log_result("Watcher log file", PASS, f"{watcher_log.stat().st_size} bytes")
    else:
        log_result("Watcher log file", FAIL)


def test_hitl_workflow():
    """Test 6: Verify Human-in-the-Loop approval workflow."""
    print("\n=== Test 6: HITL Approval Workflow ===")

    # Create a mock approval request
    approval_file = VAULT / "Pending_Approval" / "EMAIL_test_client_2026-02-15.md"
    approval_file.write_text("""---
type: approval_request
action: send_email
to: client@example.com
subject: February Invoice - $2,500
status: pending
created: 2026-02-15T10:00:00Z
---

## Email Details
- To: client@example.com
- Subject: February Invoice - $2,500
- Attachment: /Invoices/2026-02_Client_X.pdf

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
""")
    log_result("Approval request created", PASS, approval_file.name)

    # Simulate human approval (move to /Approved)
    approved_dest = VAULT / "Approved" / approval_file.name
    approval_file.rename(approved_dest)
    if approved_dest.exists():
        log_result("Human approval (file move)", PASS, "Moved to /Approved")
    else:
        log_result("Human approval (file move)", FAIL)

    # Verify orchestrator can find approved items
    from orchestrator import Orchestrator
    orch = Orchestrator(str(VAULT), dry_run=True)
    approved = orch.get_approved_items()
    if approved:
        log_result("Orchestrator detects approved items", PASS, f"{len(approved)} item(s)")
    else:
        log_result("Orchestrator detects approved items", FAIL)

    # Clean up - move to Done
    if approved_dest.exists():
        approved_dest.rename(VAULT / "Done" / approved_dest.name)
        log_result("Approved item completed", PASS, "Moved to /Done")


def test_dashboard_content():
    """Test 7: Verify Dashboard has proper structure."""
    print("\n=== Test 7: Dashboard Validation ===")

    dashboard = VAULT / "Dashboard.md"
    content = dashboard.read_text()

    # Check YAML frontmatter
    if content.startswith("---"):
        log_result("YAML frontmatter", PASS)
    else:
        log_result("YAML frontmatter", FAIL)

    # Check required sections
    sections = [
        "System Status",
        "Financial Summary",
        "Pending Messages",
        "Active Projects",
        "Needs Action Queue",
        "Recent Activity",
        "Weekly Metrics",
    ]
    for section in sections:
        if section in content:
            log_result(f"Section: {section}", PASS)
        else:
            log_result(f"Section: {section}", FAIL, "Not found")


def print_summary():
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == PASS)
    failed = sum(1 for _, s, _ in results if s == FAIL)
    total = len(results)
    print(f"  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Rate:   {passed/total*100:.0f}%" if total > 0 else "  Rate: N/A")
    print("=" * 60)

    if failed > 0:
        print("\nFailed tests:")
        for name, status, detail in results:
            if status == FAIL:
                print(f"  [FAIL] {name}: {detail}")

    return failed == 0


if __name__ == "__main__":
    print("=" * 60)
    print("AI EMPLOYEE - BRONZE TIER INTEGRATION TEST")
    print(f"Vault: {VAULT}")
    print(f"Time:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    test_vault_structure()
    test_core_files()
    test_filesystem_watcher()
    test_orchestrator()
    test_logging()
    test_hitl_workflow()
    test_dashboard_content()

    all_passed = print_summary()
    sys.exit(0 if all_passed else 1)
