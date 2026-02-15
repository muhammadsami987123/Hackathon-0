# Inbox Processor Skill

## Description
Processes items in the /Needs_Action folder of the AI Employee Obsidian vault. Reads each pending item, determines the appropriate action based on Company_Handbook.md rules, and either auto-executes safe actions or creates approval requests for sensitive ones.

## Instructions

When invoked, follow this workflow:

1. **Read** all `.md` files in `/Needs_Action/` directory
2. **For each item:**
   a. Parse the YAML frontmatter to determine `type`, `priority`, and `status`
   b. Read `Company_Handbook.md` to check applicable rules
   c. Classify the action required:
      - **Auto-approved**: File categorization, report generation, dashboard updates
      - **Approval-required**: Email sends, payments, social media posts, external actions
3. **For auto-approved actions:**
   - Execute the action (create drafts, categorize files, update logs)
   - Move the item to `/Done/`
   - Log the action to `/Logs/YYYY-MM-DD.json`
4. **For approval-required actions:**
   - Create an approval request file in `/Pending_Approval/`
   - Include clear description of the proposed action
   - Include instructions: "Move to /Approved to proceed, /Rejected to cancel"
5. **Update** `Dashboard.md` with a summary of actions taken

## Output Format
For each processed item, log:
```json
{
  "timestamp": "ISO-8601",
  "action_type": "type of action",
  "actor": "claude_code",
  "item": "source file name",
  "result": "success|pending_approval|error",
  "details": "brief description"
}
```

## Triggers
- Called by Orchestrator when new items appear in /Needs_Action
- Can be manually invoked: `/inbox-processor`

## Dependencies
- Requires access to the Obsidian vault filesystem
- Reads Company_Handbook.md for rules
- Writes to Dashboard.md, /Logs, /Pending_Approval, /Done
