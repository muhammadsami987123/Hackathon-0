# Dashboard Updater Skill

## Description
Updates the AI Employee Dashboard.md with current system status, financial summaries, pending items, active projects, and recent activity. This skill aggregates data from across the vault to provide a real-time overview.

## Instructions

When invoked, perform the following:

1. **Scan vault folders** to gather current state:
   - Count files in `/Needs_Action/` (pending items)
   - Count files in `/In_Progress/` (active items)
   - Count files in `/Pending_Approval/` (awaiting human review)
   - Count files in `/Done/` (completed today)

2. **Read financial data** from `/Accounting/` if available:
   - Current bank balance
   - MTD revenue and expenses
   - Pending invoices count

3. **Check system component status**:
   - File System Watcher: Check if process is running
   - Orchestrator: Check if process is running
   - Claude Code: Always mark as Ready if this skill is executing

4. **Update Dashboard.md** sections:
   - System Status table
   - Financial Summary table
   - Needs Action Queue table (list pending items with type and priority)
   - Recent Activity log (append latest actions)
   - Weekly Metrics

5. **Add timestamp** to frontmatter `last_updated` field

## Output Format
Update Dashboard.md in-place, preserving its markdown structure. Add a recent activity entry:
```
- [YYYY-MM-DD HH:MM] Description of activity
```

## Triggers
- Called after inbox processing completes
- Called on scheduled intervals (e.g., every hour)
- Can be manually invoked: `/dashboard-updater`

## Dependencies
- Read access to all vault folders
- Write access to Dashboard.md
