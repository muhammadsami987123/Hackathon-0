# Personal AI Employee - Bronze Tier Digital FTE

> *Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.*

A **Digital FTE (Full-Time Equivalent)** — an autonomous AI Employee that proactively manages personal and business affairs 24/7. Built with **Claude Code** as the reasoning engine and **Obsidian** as the GUI and long-term memory. This is not a chatbot; it's a senior employee who figures out how to solve the problems.

## Why a Digital FTE?

| Feature | Human FTE | Digital FTE |
|---------|-----------|-------------|
| Availability | 40 hours/week | 168 hours/week (24/7) |
| Monthly Cost | $4,000 – $8,000+ | $500 – $2,000 |
| Ramp-up Time | 3–6 Months | Instant (via SKILL.md) |
| Consistency | Variable (85–95%) | Predictable (99%+) |
| Annual Hours | ~2,000 hours | ~8,760 hours |
| Cost per Task | ~$3.00 – $6.00 | ~$0.25 – $0.50 |

**A Digital FTE works nearly 9,000 hours/year vs a human's 2,000 — an 85–90% cost saving per task.**

## Architecture: Perception → Reasoning → Action

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PERCEPTION    │     │    REASONING     │     │     ACTION      │
│   (Watchers)    │────>│  (Claude Code)   │────>│   (MCP / HITL)  │
│                 │     │                  │     │                 │
│ - File System   │     │ - Read vault     │     │ - Send emails   │
│ - Gmail         │     │ - Think & plan   │     │ - Make payments │
│ - WhatsApp      │     │ - Create plans   │     │ - Post social   │
│ - Finance       │     │ - Execute tasks  │     │ - Move files    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │   OBSIDIAN VAULT    │
                    │ (GUI + Long-Term    │
                    │      Memory)        │
                    └─────────────────────┘
```

### Components

| Component | Role | Description |
|-----------|------|-------------|
| **Obsidian Vault** | GUI + Memory | Dashboard, rules, file-based workflow engine |
| **File System Watcher** | Perception | Monitors `/Inbox` for new files, creates action items |
| **Orchestrator** | Coordination | Claims tasks (Needs_Action → In_Progress → Done) |
| **Claude Code** | Brain | Reads tasks, creates plans, executes via MCP |
| **Agent Skills** | Intelligence | Specialized skills for inbox processing, dashboard updates, plan creation |
| **HITL Approval** | Safety | Human-in-the-loop for sensitive actions (payments, emails, social posts) |
| **Web Dashboard** | Nerve Center | Real-time Flask dashboard at `localhost:5000` |

## Vault Structure

```
AI_Employee_Vault/
├── README.md                 # Vault-specific documentation
├── Dashboard.md              # Real-time system overview (status, financials)
├── Company_Handbook.md       # Rules of engagement & action boundaries
├── Business_Goals.md         # Revenue targets, key metrics, expense budgets
│
├── Inbox/                    # Drop zone — new files arrive here
├── Needs_Action/             # Items queued for AI processing
├── In_Progress/              # Items claimed and being worked on
├── Done/                     # Completed items
├── Pending_Approval/         # Awaiting human review
├── Approved/                 # Human-approved actions
├── Rejected/                 # Human-rejected actions
│
├── Plans/                    # Claude-generated execution plans
├── Logs/                     # Daily JSON audit logs (YYYY-MM-DD.json)
├── Accounting/               # Financial records & transactions
├── Invoices/                 # Generated invoices
├── Briefings/                # CEO briefings & weekly reports
├── Active_Project/           # Current project files
├── Updates/                  # System updates
│
├── scripts/                  # Python automation layer
│   ├── base_watcher.py       # Abstract watcher base class
│   ├── filesystem_watcher.py # File system monitoring (watchdog)
│   ├── orchestrator.py       # Master coordination process
│   ├── test_pipeline.py      # End-to-end pipeline tests
│   └── requirements.txt      # Python dependencies
│
└── dashboard/                # Flask web dashboard (Nerve Center)
    ├── app.py                # Flask server + API + process management
    ├── vault_reader.py       # Read-only data layer for vault state
    ├── templates/
    │   └── index.html        # Single-page dashboard with inline JS
    └── static/
        └── style.css         # Dark theme CSS
```

## Workflow: Claim-by-Move Pattern

The AI Employee uses a **file-based workflow** where Markdown files with YAML frontmatter move through folders representing states:

```
                    ┌──────────────┐
                    │    Inbox/    │  ← Files dropped here (manual or watcher)
                    └──────┬───────┘
                           │ Watcher detects
                    ┌──────▼───────┐
                    │ Needs_Action/│  ← Queued for processing
                    └──────┬───────┘
                           │ Orchestrator claims (move)
                    ┌──────▼───────┐
                    │ In_Progress/ │  ← Being worked on
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼───────┐        ┌───────▼──────────┐
       │    Done/     │        │ Pending_Approval/ │ ← Sensitive actions
       └──────────────┘        └───────┬───────────┘
                                       │ Human reviews
                            ┌──────────┼──────────┐
                            │                     │
                     ┌──────▼──────┐      ┌───────▼─────┐
                     │  Approved/  │      │  Rejected/  │
                     └─────────────┘      └─────────────┘
```

**Claim-by-move rule:** The first agent to move an item from `/Needs_Action` to `/In_Progress` owns it — other agents must ignore it.

## Human-in-the-Loop (HITL) Safety

Sensitive actions require human approval. The AI writes an approval request file:

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---

## Payment Details
- Amount: $500.00
- To: Client A

## To Approve → Move this file to /Approved
## To Reject  → Move this file to /Rejected
```

### Action Boundaries

| Action Type | Auto-Approved | Requires Approval |
|-------------|:------------:|:-----------------:|
| Read vault files | Yes | - |
| Create draft documents | Yes | - |
| Move files between folders | Yes | - |
| Update Dashboard.md | Yes | - |
| Create Plan.md files | Yes | - |
| Log activities | Yes | - |
| **Send any email** | - | Yes |
| **Make any payment** | - | Yes |
| **Post to social media** | - | Yes |
| **Delete files** | - | Yes |
| **Contact unknown parties** | - | Yes |

## Web Dashboard (Nerve Center)

A real-time Flask dashboard at `http://localhost:5000` with auto-refresh (5s polling):

| Panel | Description |
|-------|-------------|
| System Status | Watcher, Orchestrator, Claude Code indicators |
| Financial Summary | Bank balance, MTD revenue/expenses, pending invoices |
| Business Goals | Revenue progress bar + key metrics |
| Queue Management | 7 workflow folder cards with click-to-expand detail |
| Pending Approvals | Items with Approve/Reject buttons |
| Plans Viewer | Plan list with content preview |
| Activity Log | Scrollable audit log from JSON files |
| Controls | Start/Stop Watcher, Orchestrator, Refresh |

### API Endpoints

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

## Quick Start

### Prerequisites

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Active subscription | Primary reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ (free) | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts & orchestration |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers & automation |

### 1. Install Dependencies
```bash
pip install -r AI_Employee_Vault/scripts/requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Open Vault in Obsidian
Open the `AI_Employee_Vault` folder as an Obsidian vault.

### 4. Start the Web Dashboard
```bash
python AI_Employee_Vault/dashboard/app.py --port 5000
# Open http://localhost:5000
```

### 5. Start the File Watcher
```bash
python AI_Employee_Vault/scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault
```

### 6. Start the Orchestrator
```bash
python AI_Employee_Vault/scripts/orchestrator.py --vault-path ./AI_Employee_Vault --dry-run
```

### 7. Test It
Drop a file into `AI_Employee_Vault/Inbox/` and watch it get processed through the workflow.

## Hackathon Tier Progress

### Bronze Tier: Foundation (Current)
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] One working Watcher script (File System monitoring)
- [x] Claude Code reading from and writing to the vault
- [x] Basic folder structure: /Inbox, /Needs_Action, /Done
- [x] AI functionality implemented as Agent Skills
- [x] Web Dashboard (Nerve Center) at localhost:5000
- [x] Human-in-the-Loop approval workflow
- [x] JSON audit logging to /Logs

### Silver Tier: Functional Assistant (Next)
- [ ] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [ ] Automatically post on LinkedIn to generate sales
- [ ] Claude reasoning loop that creates Plan.md files
- [ ] One working MCP server for external action (e.g., sending emails)
- [ ] Basic scheduling via cron or Task Scheduler

### Gold Tier: Autonomous Employee
- [ ] Full cross-domain integration (Personal + Business)
- [ ] Odoo Community accounting integration via MCP
- [ ] Facebook/Instagram/Twitter integration
- [ ] Weekly Business Audit with CEO Briefing generation
- [ ] Ralph Wiggum loop for autonomous multi-step task completion
- [ ] Error recovery and graceful degradation

### Platinum Tier: Always-On Cloud + Local Executive
- [ ] Run AI Employee on Cloud 24/7 (Oracle/AWS VM)
- [ ] Work-Zone Specialization (Cloud drafts, Local approves)
- [ ] Synced Vault via Git between Cloud and Local
- [ ] Cloud Odoo deployment with MCP integration

## File Formats

### Vault Markdown Files (YAML Frontmatter)
```markdown
---
type: invoice
status: pending
priority: high
created: 2026-02-15
---

# Task Content Here
```

### Audit Logs (Logs/YYYY-MM-DD.json)
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

## Security

- Credentials stored in `.env` (never committed to git)
- Dry-run mode enabled by default on all scripts
- All actions logged to `/Logs/` with full audit trail
- HITL approval required for payments, emails, social posts
- Payments over $500 always require human approval
- New payee payments always require approval
- Banking credentials never stored in vault files

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Brain | [Claude Code](https://claude.com/product/claude-code) | Reasoning engine & task execution |
| Memory/GUI | [Obsidian](https://obsidian.md/) | Knowledge base, dashboard, local Markdown |
| Nerve Center | [Flask](https://flask.palletsprojects.com/) | Web dashboard at localhost:5000 |
| Perception | [watchdog](https://github.com/gorakhargosh/watchdog) | File system monitoring |
| Hands | MCP Servers | External actions (email, browser, payments) |
| Safety | HITL Pattern | File-based human approval workflow |
| Data | YAML + JSON | Frontmatter metadata + audit logs |

## License

This project was built for **Personal AI Employee Hackathon 0** (Panaversity, 2026).
