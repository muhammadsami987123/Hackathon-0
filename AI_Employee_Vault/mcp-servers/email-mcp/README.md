# Email MCP Server

This Model Context Protocol (MCP) server enables the AI Employee to send emails as part of the Silver Tier: Functional Assistant implementation.

## Capabilities

- `sendEmail`: Send an email to specified recipients
- `sendEmailDraft`: Create an email draft for review (doesn't actually send)
- `listEmails`: View recent emails (read-only, for monitoring)

## Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your email credentials

## Configuration

For Gmail users:
1. Enable 2-factor authentication
2. Generate an app password (not your regular password)
3. Use the app password in the `EMAIL_APP_PASSWORD` field

## Usage

Start the server:
```bash
npm start
```

Or run in development mode:
```bash
npm run dev
```

Then configure Claude Code to use this MCP server in your Claude Code settings.