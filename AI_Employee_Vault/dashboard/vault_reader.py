"""
Vault Reader - Read-only data layer for the AI Employee dashboard.

Reads vault folders, parses .md YAML frontmatter, and reads JSON logs
without modifying any vault state.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import yaml


# Workflow folders tracked by the dashboard
WORKFLOW_FOLDERS = [
    "Inbox", "Needs_Action", "In_Progress", "Done",
    "Pending_Approval", "Approved", "Rejected"
]

# All known folders in the vault
ALL_FOLDERS = WORKFLOW_FOLDERS + [
    "Plans", "Logs", "Accounting", "Active_Project",
    "Briefings", "Invoices", "Updates", "scripts"
]


def parse_frontmatter(filepath: Path) -> dict:
    """Parse YAML frontmatter from a .md file.

    Returns dict of YAML fields, or empty dict if no frontmatter found.
    """
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    try:
        data = yaml.safe_load(match.group(1)) or {}
        # Convert date/datetime objects to strings for JSON serialization
        for key, val in data.items():
            if hasattr(val, 'isoformat'):
                data[key] = val.isoformat()
        return data
    except yaml.YAMLError:
        return {}


def get_folder_counts(vault_path: str) -> dict:
    """Return dict of folder names -> file counts."""
    vault = Path(vault_path)
    counts = {}
    for folder in ALL_FOLDERS:
        folder_path = vault / folder
        if folder_path.is_dir():
            counts[folder] = len([
                f for f in folder_path.iterdir()
                if f.is_file() and not f.name.startswith(".")
            ])
        else:
            counts[folder] = 0
    return counts


def get_folder_items(vault_path: str, folder_name: str) -> list[dict]:
    """Return list of file info dicts for .md files in a folder."""
    folder = Path(vault_path) / folder_name
    if not folder.is_dir():
        return []

    items = []
    for f in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.name.startswith("."):
            continue
        stat = f.stat()
        item = {
            "name": f.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": f.suffix,
        }
        if f.suffix == ".md":
            item["frontmatter"] = parse_frontmatter(f)
        items.append(item)
    return items


def get_system_status(vault_path: str) -> dict:
    """Read system component statuses from Dashboard.md."""
    dashboard = Path(vault_path) / "Dashboard.md"
    status = {
        "watcher": {"status": "offline", "last_check": None},
        "orchestrator": {"status": "offline", "last_check": None},
        "claude": {"status": "offline", "last_check": None},
    }

    if not dashboard.is_file():
        return status

    text = dashboard.read_text(encoding="utf-8", errors="replace")

    # Parse the system status table
    component_map = {
        "file system watcher": "watcher",
        "watcher": "watcher",
        "orchestrator": "orchestrator",
        "claude code": "claude",
        "claude": "claude",
    }

    for line in text.split("\n"):
        if "|" not in line or "---" in line or "Component" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 3:
            component_name = parts[0].lower()
            for key, mapped in component_map.items():
                if key in component_name:
                    raw_status = parts[1].lower()
                    if "running" in raw_status or "ready" in raw_status or "✅" in parts[1]:
                        status[mapped]["status"] = "running"
                    elif "pending" in raw_status or "🟡" in parts[1]:
                        status[mapped]["status"] = "pending"
                    else:
                        status[mapped]["status"] = "offline"
                    status[mapped]["last_check"] = parts[2] if parts[2] != "-" else None
                    break

    return status


def get_recent_logs(vault_path: str, limit: int = 50) -> list[dict]:
    """Read recent JSON log entries from Logs/YYYY-MM-DD.json files."""
    logs_dir = Path(vault_path) / "Logs"
    if not logs_dir.is_dir():
        return []

    all_entries = []

    # Get all JSON log files sorted by name descending (most recent first)
    log_files = sorted(logs_dir.glob("*.json"), reverse=True)

    for log_file in log_files:
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
            if isinstance(entries, list):
                all_entries.extend(entries)
        except (json.JSONDecodeError, OSError):
            continue

        if len(all_entries) >= limit:
            break

    # Sort by timestamp descending, limit results
    all_entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return all_entries[:limit]


def get_dashboard_data(vault_path: str) -> dict:
    """Parse structured sections from Dashboard.md."""
    dashboard = Path(vault_path) / "Dashboard.md"
    if not dashboard.is_file():
        return {}

    text = dashboard.read_text(encoding="utf-8", errors="replace")
    data = {"raw": text, "sections": {}}

    current_section = None
    section_lines = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_section:
                data["sections"][current_section] = "\n".join(section_lines)
            current_section = line[3:].strip()
            section_lines = []
        elif current_section:
            section_lines.append(line)

    if current_section:
        data["sections"][current_section] = "\n".join(section_lines)

    # Parse financial summary table if present
    fin = data["sections"].get("Financial Summary", "")
    data["financial"] = _parse_table_to_dict(fin)

    return data


def _parse_table_to_dict(table_text: str) -> dict:
    """Parse a markdown table with Metric|Value columns into a dict."""
    result = {}
    for line in table_text.split("\n"):
        if "|" not in line or "---" in line or "Metric" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        if len(parts) >= 2:
            result[parts[0]] = parts[1]
    return result


def get_business_goals(vault_path: str) -> dict:
    """Parse Business_Goals.md for revenue targets and metrics."""
    goals_file = Path(vault_path) / "Business_Goals.md"
    if not goals_file.is_file():
        return {}

    text = goals_file.read_text(encoding="utf-8", errors="replace")
    goals = {
        "frontmatter": parse_frontmatter(goals_file),
        "revenue_target": None,
        "current_mtd": None,
        "metrics": [],
        "expenses": [],
    }

    # Extract revenue target
    for line in text.split("\n"):
        if "monthly goal" in line.lower():
            match = re.search(r"\$[\d,]+", line)
            if match:
                goals["revenue_target"] = match.group(0)
        elif "current mtd" in line.lower():
            match = re.search(r"\$[\d,]+", line)
            if match:
                goals["current_mtd"] = match.group(0)

    # Parse key metrics table
    in_metrics = False
    in_expenses = False
    for line in text.split("\n"):
        if "Key Metrics" in line:
            in_metrics = True
            in_expenses = False
            continue
        elif "Monthly Expense" in line:
            in_expenses = True
            in_metrics = False
            continue
        elif line.startswith("##"):
            in_metrics = False
            in_expenses = False
            continue

        if (in_metrics or in_expenses) and "|" in line and "---" not in line and "Metric" not in line and "Category" not in line:
            parts = [p.strip() for p in line.split("|")]
            parts = [p for p in parts if p]
            if in_metrics and len(parts) >= 3:
                goals["metrics"].append({
                    "metric": parts[0],
                    "target": parts[1],
                    "alert": parts[2] if len(parts) > 2 else "",
                })
            elif in_expenses and len(parts) >= 3:
                goals["expenses"].append({
                    "category": parts[0],
                    "budget": parts[1],
                    "alert": parts[2] if len(parts) > 2 else "",
                })

    return goals


def get_pending_approvals(vault_path: str) -> list[dict]:
    """Return items in Pending_Approval/ with full frontmatter and preview."""
    folder = Path(vault_path) / "Pending_Approval"
    if not folder.is_dir():
        return []

    items = []
    for f in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or f.name.startswith("."):
            continue
        item = {
            "name": f.name,
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        }
        if f.suffix == ".md":
            item["frontmatter"] = parse_frontmatter(f)
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
                # Strip frontmatter for preview
                stripped = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
                item["preview"] = stripped[:300]
            except OSError:
                item["preview"] = ""
        items.append(item)
    return items


def get_plans(vault_path: str) -> list[dict]:
    """Return plan files from Plans/ with frontmatter and preview."""
    folder = Path(vault_path) / "Plans"
    if not folder.is_dir():
        return []

    items = []
    for f in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not f.is_file() or not f.name.endswith(".md"):
            continue
        item = {
            "name": f.name,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            "frontmatter": parse_frontmatter(f),
        }
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            stripped = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
            item["preview"] = stripped[:500]
        except OSError:
            item["preview"] = ""
        items.append(item)
    return items
