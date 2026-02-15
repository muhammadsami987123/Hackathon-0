# AI Employee Vault

An autonomous AI Employee system (Bronze Tier Digital FTE) built with Claude Code and Obsidian. The vault serves as both the long-term memory and the central nervous system for the AI Employee, managing tasks, finances, communications, and business operations through a file-based workflow.

## Quick Start

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Start the web dashboard
python dashboard/app.py --port 5000

# Open http://localhost:5000 in your browser
```

## Architecture

The system operates on a **file-based workflow** pattern. Markdown files with YAML frontmatter move through folders representing workflow states. Three core components work together:

- **File System Watcher** — Monitors the vault for new/changed files and logs events
- **Orchestrator** — Claims tasks from `Needs_Action/`, creates plans, and invokes Claude Code
- **Web Dashboard** — Real-time Nerve Center UI at `localhost:5000` with auto-refresh

## Vault Structure

```
AI_Employee_Vault/
├── README.md               # This file
├── Company_Handbook.md      # Rules of engagement, policies, action boundaries
├── Business_Goals.md        # Revenue targets, key metrics, expense budgets
├── Dashboard.md             # System status, financial summary, active projects
│
├── Inbox/                   # New incoming items (drop zone)
├── Needs_Action/            # Items queued for AI processing
├── In_Progress/             # Items currently being worked on
├── Done/                    # Completed items
├── Pending_Approval/        # Items awaiting human review
├── Approved/                # Human-approved items
├── Rejected/                # Human-rejected items
│
├── Plans/                   # AI-generated execution plans
├── Logs/                    # Daily JSON audit logs (YYYY-MM-DD.json)
├── Accounting/              # Financial records
├── Invoices/                # Invoice documents
├── Active_Project/          # Current project files
├── Briefings/               # Generated briefings and reports
├── Updates/                 # Status updates
│
├── scripts/                 # Python automation scripts
│   ├── base_watcher.py      # Base class for file watchers
│   ├── filesystem_watcher.py # Monitors vault for file changes
│   ├── orchestrator.py      # Claims and processes tasks autonomously
│   ├── test_pipeline.py     # End-to-end pipeline tests
│   └── requirements.txt     # Python dependencies
│
└── dashboard/               # Flask web dashboard
    ├── app.py               # Flask server (routes + API + process management)
    ├── vault_reader.py      # Read-only data layer for vault state
    ├── templates/
    │   └── index.html       # Single-page dashboard UI
    └── static/
        └── style.css        # Dark theme CSS
```

## Workflow

The AI Employee follows a **claim-by-move** pattern:

```
Inbox/ --> Needs_Action/ --> In_Progress/ --> Done/
                                |
                                +--> Pending_Approval/ --> Approved/
                                                      --> Rejected/
```

1. Files arrive in `Inbox/` (manually or via integrations)
2. The **Watcher** detects new files and moves them to `Needs_Action/`
3. The **Orchestrator** claims a task by moving it to `In_Progress/`
4. A plan is created in `Plans/` and Claude Code executes it
5. Results go to `Done/` or `Pending_Approval/` for human review
6. Humans approve or reject via the dashboard

## Web Dashboard

The dashboard at `http://localhost:5000` provides 8 panels:

| Panel | Description |
|-------|-------------|
| System Status | Watcher, Orchestrator, and Claude Code status indicators |
| Financial Summary | Bank balance, MTD revenue/expenses, pending invoices |
| Business Goals | Revenue progress bar and key metrics |
| Queue Management | File counts across all 7 workflow folders |
| Pending Approvals | Items awaiting review with Approve/Reject buttons |
| Plans Viewer | Plan list with content preview |
| Activity Log | Scrollable audit log from JSON log files |
| Controls | Start/Stop Watcher, Orchestrator, and Refresh |

### Dashboard API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System overview, folder counts, financials |
| GET | `/api/queue/<folder>` | Files in a workflow folder |
| GET | `/api/logs` | Recent audit log entries |
| GET | `/api/approvals` | Pending approval items |
| GET | `/api/plans` | Plans with preview content |
| GET | `/api/goals` | Business goals and metrics |
| POST | `/api/approve/<filename>` | Approve a pending item |
| POST | `/api/reject/<filename>` | Reject a pending item |
| POST | `/api/process/start` | Start watcher/orchestrator |
| POST | `/api/process/stop` | Stop running processes |

## Key Rules (from Company Handbook)

### Auto-Approved Actions
- Reading files, creating drafts, moving files between folders
- Updating Dashboard.md, creating plans, logging activities

### Requires Human Approval
- Sending emails, making payments, posting to social media
- Deleting files, contacting unknown parties, external system actions

### Financial Safety
- Payments over $500 require human approval
- New payee payments always require approval
- All financial actions logged to `/Logs`

## Dependencies

```
watchdog>=4.0.0     # File system monitoring
python-dotenv>=1.0.0 # Environment configuration
flask>=3.0.0        # Web dashboard server
pyyaml>=6.0         # YAML frontmatter parsing
```

## File Format

All vault markdown files use YAML frontmatter:

```markdown
---
title: Example Task
type: invoice
status: pending
priority: high
created: 2026-02-15
---

# Task Content Here
```

Audit logs use JSON arrays in `Logs/YYYY-MM-DD.json`:

```json
[
  {
    "timestamp": "2026-02-15T22:57:26",
    "actor": "orchestrator",
    "action_type": "task_claimed",
    "details": { "file": "example.md", "from": "Needs_Action", "to": "In_Progress" }
  }
]
```

## Running Components Individually

```bash
# File System Watcher only
python scripts/filesystem_watcher.py --vault-path .

# Orchestrator only
python scripts/orchestrator.py --vault-path . --interval 10

# Dashboard only
python dashboard/app.py --port 5000 --debug

# All via dashboard controls
# Click "Start All" in the Controls panel at http://localhost:5000
```
