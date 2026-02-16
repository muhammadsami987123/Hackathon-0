# Scheduler Skill

## Description
Manages scheduled tasks for the AI Employee, including regular reporting, social media posting, and periodic reviews. This skill creates system scheduling configurations (cron jobs on Unix, Task Scheduler on Windows) to automate recurring tasks.

## Instructions

When invoked, perform the following:

1. **Read** Business_Goals.md and Company_Handbook.md to identify recurring tasks that need scheduling:
   - Daily briefings (e.g., "Monday Morning CEO Briefing")
   - Weekly reports
   - Monthly reviews
   - Social media posting schedules
   - Financial audits

2. **Determine** appropriate scheduling intervals based on business requirements:
   - Daily reports: Run at 8:00 AM
   - Weekly audits: Run on Sundays at 11:00 PM
   - Monthly reviews: Run on last day of month at 11:00 PM
   - Social media: Varies by platform and business needs

3. **Create** scheduling configurations:
   - On Unix/Linux/macOS: Create or update cron jobs
   - On Windows: Create or update Task Scheduler entries
   - For cloud deployment: Create appropriate scheduling service configurations

4. **Document** all scheduled tasks in the system for monitoring:
   - Log scheduled tasks to /Logs/scheduled_tasks.json
   - Update Dashboard.md with scheduled task summary
   - Create alerts for failed scheduled tasks

5. **Monitor** scheduled tasks for failures and create remediation items in /Needs_Action/

## Scheduling Examples

### Daily Business Briefing
- Frequency: Daily at 8:00 AM
- Action: Generate daily business summary and update Dashboard.md
- Command: `python briefing_generator.py`

### Weekly CEO Report
- Frequency: Sundays at 11:00 PM
- Action: Generate weekly summary of revenue, bottlenecks, and suggestions
- Command: `claude --print "Generate weekly CEO briefing following Business_Handbook.md format"`

### Social Media Posts
- Frequency: 3 times per week (Tues/Thurs/Sat) at 10:00 AM
- Action: Create LinkedIn posts based on Business_Goals.md
- Creates approval request in /Pending_Approval/

## Output Format
For each scheduled task, log:
```json
{
  "task_id": "unique_identifier",
  "name": "Task description",
  "schedule": "cron_expression_or_schedule_description",
  "command": "command_to_execute",
  "target": "target_system",
  "enabled": true,
  "last_run": "ISO-8601_timestamp",
  "next_run": "ISO-8601_timestamp"
}
```

## Triggers
- Called when Business_Goals.md is updated
- Called when new recurring tasks are identified
- Can be manually invoked: `/scheduler`

## Dependencies
- Read access to Business_Goals.md and Company_Handbook.md
- System access to create cron jobs or Task Scheduler entries
- Write access to system configuration files
- Access to all scripts and tools that need scheduling