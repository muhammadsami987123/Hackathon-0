"""
AI Employee Web Dashboard — Flask Application

Single-file server providing:
- HTML dashboard at GET /
- JSON API endpoints for vault state
- Process management for watcher/orchestrator
- Approve/reject workflow actions

Usage:
    python app.py [--vault-path /path/to/vault] [--port 5000] [--debug]
"""

import argparse
import json
import shutil
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

# Ensure the dashboard package is importable
sys.path.insert(0, str(Path(__file__).parent))
import vault_reader

app = Flask(__name__)

# Global state
VAULT_PATH = str(Path(__file__).parent.parent)  # Default: AI_Employee_Vault/
running_processes: dict[str, subprocess.Popen] = {}


# --------------- Page Routes ---------------

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


# --------------- API Routes ---------------

@app.route("/api/status")
def api_status():
    """System overview: folder counts, system status, financial summary."""
    folder_counts = vault_reader.get_folder_counts(VAULT_PATH)
    system_status = vault_reader.get_system_status(VAULT_PATH)
    dashboard_data = vault_reader.get_dashboard_data(VAULT_PATH)

    # Overlay live process info
    for name in ("watcher", "orchestrator"):
        proc = running_processes.get(name)
        if proc and proc.poll() is None:
            system_status[name]["status"] = "running"
            system_status[name]["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        elif proc and proc.poll() is not None:
            # Process exited
            system_status[name]["status"] = "offline"
            running_processes.pop(name, None)

    return jsonify({
        "folder_counts": folder_counts,
        "system_status": system_status,
        "financial": dashboard_data.get("financial", {}),
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/queue/<folder>")
def api_queue(folder):
    """List files in a specific workflow folder."""
    allowed = vault_reader.WORKFLOW_FOLDERS + ["Plans", "Logs"]
    if folder not in allowed:
        return jsonify({"error": f"Folder '{folder}' not accessible"}), 400

    items = vault_reader.get_folder_items(VAULT_PATH, folder)
    return jsonify({"folder": folder, "items": items, "count": len(items)})


@app.route("/api/logs")
def api_logs():
    """Recent audit log entries."""
    limit = request.args.get("limit", 50, type=int)
    limit = min(limit, 200)
    logs = vault_reader.get_recent_logs(VAULT_PATH, limit=limit)
    return jsonify({"logs": logs, "count": len(logs)})


@app.route("/api/approvals")
def api_approvals():
    """Pending approval items with details."""
    items = vault_reader.get_pending_approvals(VAULT_PATH)
    return jsonify({"items": items, "count": len(items)})


@app.route("/api/plans")
def api_plans():
    """List of plans with preview content."""
    plans = vault_reader.get_plans(VAULT_PATH)
    return jsonify({"plans": plans, "count": len(plans)})


@app.route("/api/goals")
def api_goals():
    """Business goals and metrics."""
    goals = vault_reader.get_business_goals(VAULT_PATH)
    return jsonify(goals)


# --------------- Action Routes ---------------

@app.route("/api/approve/<filename>", methods=["POST"])
def api_approve(filename):
    """Move file from Pending_Approval → Approved."""
    src = Path(VAULT_PATH) / "Pending_Approval" / filename
    if not src.is_file():
        return jsonify({"error": f"File not found: {filename}"}), 404

    dest_dir = Path(VAULT_PATH) / "Approved"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    shutil.move(str(src), str(dest))

    _log_action("dashboard_approve", {
        "item": filename,
        "from": "Pending_Approval",
        "to": "Approved",
    })

    return jsonify({"status": "approved", "item": filename})


@app.route("/api/reject/<filename>", methods=["POST"])
def api_reject(filename):
    """Move file from Pending_Approval → Rejected."""
    src = Path(VAULT_PATH) / "Pending_Approval" / filename
    if not src.is_file():
        return jsonify({"error": f"File not found: {filename}"}), 404

    dest_dir = Path(VAULT_PATH) / "Rejected"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    shutil.move(str(src), str(dest))

    _log_action("dashboard_reject", {
        "item": filename,
        "from": "Pending_Approval",
        "to": "Rejected",
    })

    return jsonify({"status": "rejected", "item": filename})


# --------------- Process Management ---------------

@app.route("/api/process/start", methods=["POST"])
def api_process_start():
    """Start watcher and/or orchestrator as subprocesses."""
    data = request.get_json(silent=True) or {}
    process_name = data.get("name", "all")
    scripts_dir = Path(VAULT_PATH) / "scripts"
    started = []

    if process_name in ("watcher", "all"):
        if "watcher" not in running_processes or running_processes["watcher"].poll() is not None:
            proc = subprocess.Popen(
                [sys.executable, str(scripts_dir / "filesystem_watcher.py"),
                 "--vault-path", VAULT_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            running_processes["watcher"] = proc
            started.append("watcher")
            _log_action("process_started", {"process": "watcher", "pid": proc.pid})

    if process_name in ("orchestrator", "all"):
        if "orchestrator" not in running_processes or running_processes["orchestrator"].poll() is not None:
            proc = subprocess.Popen(
                [sys.executable, str(scripts_dir / "orchestrator.py"),
                 "--vault-path", VAULT_PATH, "--interval", "10"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            running_processes["orchestrator"] = proc
            started.append("orchestrator")
            _log_action("process_started", {"process": "orchestrator", "pid": proc.pid})

    return jsonify({"started": started})


@app.route("/api/process/stop", methods=["POST"])
def api_process_stop():
    """Stop running subprocesses."""
    data = request.get_json(silent=True) or {}
    process_name = data.get("name", "all")
    stopped = []

    targets = list(running_processes.keys()) if process_name == "all" else [process_name]

    for name in targets:
        proc = running_processes.get(name)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            stopped.append(name)
            _log_action("process_stopped", {"process": name})
        running_processes.pop(name, None)

    return jsonify({"stopped": stopped})


@app.route("/api/process/status")
def api_process_status():
    """Return status of managed subprocesses."""
    statuses = {}
    for name, proc in list(running_processes.items()):
        if proc.poll() is None:
            statuses[name] = {"status": "running", "pid": proc.pid}
        else:
            statuses[name] = {"status": "stopped", "exit_code": proc.returncode}
            running_processes.pop(name, None)
    return jsonify(statuses)


# --------------- Helpers ---------------

def _log_action(action_type: str, details: dict):
    """Append an entry to the daily JSON audit log."""
    logs_dir = Path(VAULT_PATH) / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"

    entries = []
    if log_file.exists():
        try:
            entries = json.loads(log_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append({
        "timestamp": datetime.now().isoformat(),
        "actor": "dashboard",
        "action_type": action_type,
        "details": details,
    })
    log_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def cleanup_processes():
    """Terminate all managed subprocesses on shutdown."""
    for name, proc in running_processes.items():
        if proc.poll() is None:
            proc.terminate()


# --------------- Main ---------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Web Dashboard")
    parser.add_argument(
        "--vault-path",
        default=str(Path(__file__).parent.parent),
        help="Path to the AI Employee Vault (default: parent of dashboard/)",
    )
    parser.add_argument(
        "--port", type=int, default=5000,
        help="Port to run on (default: 5000)",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run in debug mode",
    )
    args = parser.parse_args()

    VAULT_PATH = args.vault_path
    print(f"AI Employee Dashboard")
    print(f"  Vault: {VAULT_PATH}")
    print(f"  URL:   http://localhost:{args.port}")
    print()

    import atexit
    atexit.register(cleanup_processes)

    app.run(host="0.0.0.0", port=args.port, debug=args.debug)
