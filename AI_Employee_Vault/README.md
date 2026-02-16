# AI Employee Vault - Silver Tier: Functional Assistant

An autonomous AI Employee system (Silver Tier Digital FTE) built with Claude Code and Obsidian. The vault serves as both the long-term memory and the central nervous system for the AI Employee, managing tasks, finances, communications, and business operations through a file-based workflow. Enhanced with multiple watchers, MCP servers, and human-in-the-loop approval workflows.

## Quick Start

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Start the web dashboard
python dashboard/app.py --port 5000

# Open http://localhost:5000 in your browser
```

## Architecture

The system operates on a **file-based workflow** pattern. Markdown files with YAML frontmatter move through folders representing workflow states. The Silver Tier implementation includes multiple components working together:

- **Multiple Watchers** — Monitor external sources including: File system, Gmail, WhatsApp, and LinkedIn
- **Orchestrator** — Claims tasks from `Needs_Action/`, creates plans, and invokes Claude Code
- **MCP Servers** — Execute external actions (e.g., sending emails) with human approval when needed
- **Web Dashboard** — Real-time Nerve Center UI at `localhost:5000` with auto-refresh
- **Skills System** — Agent-based functionality for specialized tasks (LinkedIn posting, scheduling, etc.)
- **Human-in-the-Loop** — Approval workflows for sensitive actions in `/Pending_Approval/`

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
│   ├── gmail_watcher.py     # Monitors Gmail for new messages
│   ├── whatsapp_watcher.py  # Monitors WhatsApp Web for messages
│   ├── linkedin_watcher.py  # Monitors LinkedIn for messages and connections
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

## Silver Tier Workflow

The AI Employee follows a **claim-by-move** pattern with enhanced approval workflows:

```
External Sources (Gmail, WhatsApp, LinkedIn, Files) -->
Inbox/ --> Needs_Action/ --> In_Progress/ --> Done/
                                |
                                +--> Pending_Approval/ --> Approved/ --> MCP Action
                                                      --> Rejected/
```

### New Silver Tier Capabilities:
- **Multi-Source Monitoring**: Watchers monitor Gmail, WhatsApp, LinkedIn, and file system
- **MCP Integration**: Email MCP server handles external actions like sending emails
- **LinkedIn Automation**: Automated posting for business generation (with approval)
- **Scheduling System**: Automated recurring tasks and reports
- **Enhanced Skills**: Specialized agent skills for different tasks

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

### Python Dependencies
```
watchdog>=4.0.0     # File system monitoring
python-dotenv>=1.0.0 # Environment configuration
flask>=3.0.0        # Web dashboard server
pyyaml>=6.0         # YAML frontmatter parsing
google-auth          # Gmail API authentication
google-auth-oauthlib # Gmail OAuth
google-api-python-client # Gmail API client
playwright           # Browser automation for WhatsApp/LinkedIn
```

### Node.js Dependencies (MCP Servers)
```
@modelcontextprotocol/sdk # MCP server framework
nodemailer               # Email sending
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

## Running: Bronze Tier vs Silver Tier

### Bronze Tier: Foundation Setup
The Bronze Tier provides the core AI Employee functionality with file system monitoring:

```bash
# 1. Install basic dependencies
pip install -r scripts/requirements.txt

# 2. Start the core components
python scripts/filesystem_watcher.py --vault-path .
python scripts/orchestrator.py --vault-path . --interval 10

# 3. Start the web dashboard to monitor activity
python dashboard/app.py --port 5000
# Open http://localhost:5000 to see the dashboard

# 4. Or use the dashboard controls
# Click "Start All" in the Controls panel at http://localhost:5000
```

### Silver Tier: Functional Assistant
The Silver Tier adds multiple watchers, MCP servers, and LinkedIn automation:

```bash
# 1. Install all dependencies (Bronze + Silver)
pip install -r scripts/requirements.txt
cd mcp-servers/email-mcp && npm install

# 2. Install Playwright browsers (for WhatsApp/LinkedIn)
playwright install

# 3. Set up MCP server credentials (copy and configure)
cp mcp-servers/email-mcp/.env.example mcp-servers/email-mcp/.env
# Update .env with your email credentials

# 4. Start Bronze Tier components (minimum requirement)
python scripts/orchestrator.py --vault-path . --interval 10
python dashboard/app.py --port 5000

# 5. Start Silver Tier watchers (choose based on your needs)
# File System Watcher (always recommended)
python scripts/filesystem_watcher.py --vault-path .

# Gmail Watcher (requires Gmail API setup)
python scripts/gmail_watcher.py --vault-path .

# WhatsApp Watcher (requires browser login - run with --no-headless first)
python scripts/whatsapp_watcher.py --vault-path . --no-headless  # For initial login
# Then for regular use (after login):
python scripts/whatsapp_watcher.py --vault-path .

# LinkedIn Watcher (requires browser login - run with --no-headless first)
python scripts/linkedin_watcher.py --vault-path . --no-headless  # For initial login
# Then for regular use (after login):
python scripts/linkedin_watcher.py --vault-path .

# 6. Start MCP Server for email capabilities
cd mcp-servers/email-mcp && npm start

# 7. Monitor Dashboard.md and /Pending_Approval/ for human review items
```

### Quick Start: Complete Silver Tier
For a complete Silver Tier setup:

```bash
# 1. Install dependencies
pip install -r scripts/requirements.txt
cd mcp-servers/email-mcp && npm install && cd ../..
playwright install

# 2. Configure MCP server (optional but recommended)
cp mcp-servers/email-mcp/.env.example mcp-servers/email-mcp/.env

# 3. Start all core components
python scripts/orchestrator.py --vault-path . &
python dashboard/app.py --port 5000 &

# 4. Start all watchers (after initial browser logins if needed)
python scripts/filesystem_watcher.py --vault-path . &
python scripts/gmail_watcher.py --vault-path . &
# For WhatsApp/LinkedIn, first run with --no-headless to log in manually:
# python scripts/whatsapp_watcher.py --vault-path . --no-headless
# python scripts/linkedin_watcher.py --vault-path . --no-headless

# 5. MCP Server (in separate terminal)
cd mcp-servers/email-mcp && npm start
```

### Web Dashboard Usage
The dashboard at `http://localhost:5000` provides real-time monitoring for both tiers:
- **Bronze Tier**: Monitor basic system status, queue management, and activity logs
- **Silver Tier**: Additional panels for pending approvals, enhanced queue management across all 7 folders, and monitoring of all active watchers
