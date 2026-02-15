# Plan Creator Skill

## Description
Creates structured Plan.md files in the /Plans folder when the AI Employee needs to execute multi-step tasks. Plans break down complex actions into checkboxes, identify approval requirements, and provide Claude with a clear execution roadmap.

## Instructions

When invoked with a task description, create a plan file:

1. **Analyze the task** to identify:
   - What needs to be done (objective)
   - What information is needed (inputs)
   - What steps are required (actions)
   - What approvals are needed (HITL checkpoints)
   - What the success criteria are (completion)

2. **Create Plan file** at `/Plans/PLAN_{description}_{timestamp}.md` with this structure:

```markdown
---
created: {ISO-8601 timestamp}
source: {triggering file or request}
status: pending
estimated_steps: {number}
requires_approval: {true/false}
---

## Objective
{Clear statement of what needs to be accomplished}

## Context
{Relevant background information}

## Steps
- [ ] Step 1: {description}
- [ ] Step 2: {description}
- [ ] Step 3: {description} (REQUIRES APPROVAL)
- [ ] Step 4: {description}

## Approval Required
{List any steps that need human approval and why}

## Success Criteria
- {Criterion 1}
- {Criterion 2}

## Rollback Plan
{What to do if something goes wrong}
```

3. **Check Company_Handbook.md** to determine which steps need approval
4. **Log** plan creation to `/Logs/`

## Triggers
- Called when Orchestrator encounters a complex multi-step task
- Called when a Watcher detects an item requiring planning
- Can be manually invoked: `/plan-creator`

## Dependencies
- Read access to Company_Handbook.md and Business_Goals.md
- Write access to /Plans and /Logs
