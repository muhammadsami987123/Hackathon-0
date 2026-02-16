# AI Employee Project - Claude Code Instructions

## Project Overview
This is a Silver Tier: Functional Assistant Digital FTE (Full-Time Equivalent) - an autonomous AI Employee built with Claude Code and Obsidian.

## Key Paths
- **Vault**: `./AI_Employee_Vault/`
- **Scripts**: `./AI_Employee_Vault/scripts/`
- **Skills**: `./.claude/skills/`
- **Rules**: `./AI_Employee_Vault/Company_Handbook.md`

## Working With the Vault
- Always read `Company_Handbook.md` before taking any action
- Log all actions to `/Logs/YYYY-MM-DD.json`
- Update `Dashboard.md` after completing work
- Use the claim-by-move pattern: move items from `/Needs_Action` to `/In_Progress` before working on them
- Create approval files in `/Pending_Approval` for sensitive actions
- Never auto-approve payments, email sends, or social media posts

## Conventions
- Python scripts use argparse with `--dry-run` and `--vault-path` flags
- All watchers extend `BaseWatcher` from `base_watcher.py`
- YAML frontmatter in all vault .md files
- JSON audit logs with timestamp, actor, action_type, details, result
