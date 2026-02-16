# LinkedIn Poster Skill

## Description
Automatically posts updates to LinkedIn on behalf of the user to generate business. This skill reads from Business_Goals.md to understand posting guidelines and creates appropriate content based on company objectives.

## Instructions

When invoked, follow this workflow:

1. **Read** Business_Goals.md to understand:
   - Current business objectives
   - Target audience
   - Content guidelines
   - Post frequency requirements

2. **Check** existing posts to avoid duplication and maintain appropriate frequency

3. **Generate** LinkedIn post content following these guidelines:
   - Professional tone consistent with company brand
   - Focus on value for followers
   - Include relevant hashtags (typically 3-5)
   - Follow LinkedIn best practices for engagement

4. **Create** an approval request for the post:
   - Save draft content to `/Pending_Approval/`
   - Use format: `LINKEDIN_POST_{YYYYMMDD}_{description}.md`
   - Include clear title and content preview

5. **Wait for approval** by monitoring for the file to be moved to `/Approved/`

6. **When approved**, send the MCP command to post to LinkedIn using the LinkedIn MCP server

## Output Format

When creating a draft:
```json
{
  "type": "linkedin_post_request",
  "title": "Brief descriptive title",
  "content": "Full post content",
  "hashtags": ["list", "of", "hashtags"],
  "target_audience": "Description of intended audience",
  "approval_status": "pending"
}
```

## Triggers
- Called on scheduled intervals to maintain regular posting
- Called when Business_Goals.md is updated
- Can be manually invoked: `/linkedin-poster`

## Dependencies
- Requires access to Business_Goals.md for content guidelines
- Requires LinkedIn MCP server for posting capabilities
- Creates files in /Pending_Approval/
- Reads Company_Handbook.md for compliance requirements

## Compliance
- All posts require human approval before publishing
- Follows Company_Handbook.md guidelines for external communications
- Respects LinkedIn's terms of service