# Personal AI Employee - Bronze Tier

A local-first, agent-driven Digital FTE (Full-Time Equivalent) built with Claude Code and Obsidian.

## Architecture

```
Perception (Watchers) → Obsidian Vault → Reasoning (Claude Code) → Action (MCP/HITL)
```

### Components
- **Obsidian Vault** - Knowledge base, dashboard, and file-based workflow engine
- **File System Watcher** - Monitors `/Inbox` for new files, creates action items
- **Orchestrator** - Master process that coordinates the Needs_Action → In_Progress → Done workflow
- **Agent Skills** - Claude Code skills for inbox processing, dashboard updates, and plan creation
- **Human-in-the-Loop** - File-based approval system for sensitive actions

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time system overview
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Objectives and metrics
├── Inbox/                    # Drop files here for processing
├── Needs_Action/             # Items awaiting processing
├── In_Progress/              # Items being processed (claim-by-move)
├── Done/                     # Completed items
├── Plans/                    # Claude-generated execution plans
├── Pending_Approval/         # Items needing human approval
├── Approved/                 # Human-approved actions
├── Rejected/                 # Human-rejected actions
├── Logs/                     # Audit logs (JSON)
├── Accounting/               # Financial data
├── Briefings/                # CEO briefings
├── Invoices/                 # Generated invoices
├── Active_Project/           # Project-based work
├── Updates/                  # System updates
└── scripts/
    ├── base_watcher.py       # Abstract watcher base class
    ├── filesystem_watcher.py # File system monitoring
    ├── orchestrator.py       # Master coordination process
    └── requirements.txt      # Python dependencies
```

## Quick Start

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

### 4. Start the File Watcher
```bash
python AI_Employee_Vault/scripts/filesystem_watcher.py --vault-path ./AI_Employee_Vault
```

### 5. Start the Orchestrator
```bash
python AI_Employee_Vault/scripts/orchestrator.py --vault-path ./AI_Employee_Vault --dry-run
```

### 6. Test It
Drop a file into `AI_Employee_Vault/Inbox/` and watch it get processed.

## Tier: Bronze (Foundation)
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] One working Watcher script (File System monitoring)
- [x] Claude Code reading from and writing to the vault
- [x] Basic folder structure: /Inbox, /Needs_Action, /Done
- [x] AI functionality implemented as Agent Skills

## Security
- Credentials stored in `.env` (never committed)
- Dry-run mode enabled by default
- All actions logged to `/Logs/`
- HITL approval required for sensitive actions

## Built With
- [Claude Code](https://claude.com/product/claude-code) - Primary reasoning engine
- [Obsidian](https://obsidian.md/) - Knowledge base & dashboard
- [Python](https://www.python.org/) - Watcher scripts & orchestration
- [watchdog](https://github.com/gorakhargosh/watchdog) - File system monitoring
