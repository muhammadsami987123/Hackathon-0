const { Server, StdioServerTransport } = require('@modelcontextprotocol/sdk');
const nodemailer = require('nodemailer');
require('dotenv').config();

// Create a transporter for sending emails
const transporter = nodemailer.createTransporter({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: process.env.SMTP_PORT || 587,
  secure: false, // true for 465, false for other ports
  auth: {
    user: process.env.EMAIL_ADDRESS,
    pass: process.env.EMAIL_APP_PASSWORD, // Use app password for Gmail
  },
});

// Verify the transporter configuration
transporter.verify((error, success) => {
  if (error) {
    console.error('Email transporter configuration error:', error);
  } else {
    console.log('Email transporter is ready to send messages');
  }
});

// Create MCP server
const server = new Server({
  name: "email-mcp",
  version: "1.0.0"
});

// Define the sendEmail capability
server.capability("sendEmail", {
  description: "Send an email to specified recipients",
  inputSchema: {
    type: "object",
    properties: {
      to: {
        type: "array",
        items: { type: "string" },
        description: "Array of recipient email addresses"
      },
      subject: { type: "string", description: "Email subject line" },
      body: { type: "string", description: "Email body content (HTML or plain text)" },
      cc: {
        type: "array",
        items: { type: "string" },
        description: "Array of CC recipients (optional)"
      },
      bcc: {
        type: "array",
        items: { type: "string" },
        description: "Array of BCC recipients (optional)"
      },
      attachments: {
        type: "array",
        items: {
          type: "object",
          properties: {
            filename: { type: "string" },
            path: { type: "string" } // Path to file to attach
          }
        },
        description: "Array of file attachments (optional)"
      }
    },
    required: ["to", "subject", "body"]
  },
  handler: async ({ params }) => {
    try {
      // Prepare email options
      const mailOptions = {
        from: process.env.EMAIL_ADDRESS,
        to: params.to.join(', '),
        subject: params.subject,
        html: params.body,
      };

      // Add CC if provided
      if (params.cc && params.cc.length > 0) {
        mailOptions.cc = params.cc.join(', ');
      }

      // Add BCC if provided
      if (params.bcc && params.bcc.length > 0) {
        mailOptions.bcc = params.bcc.join(', ');
      }

      // Add attachments if provided
      if (params.attachments && params.attachments.length > 0) {
        mailOptions.attachments = params.attachments.map(att => ({
          filename: att.filename,
          path: att.path
        }));
      }

      // Send the email
      const info = await transporter.sendMail(mailOptions);

      return {
        success: true,
        messageId: info.messageId,
        recipients: params.to,
        subject: params.subject,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error("Error sending email:", error);
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
});

// Define the sendEmailDraft capability (does not send, just returns what would be sent)
server.capability("sendEmailDraft", {
  description: "Create a draft of an email (does not send, for review purposes)",
  inputSchema: {
    type: "object",
    properties: {
      to: {
        type: "array",
        items: { type: "string" },
        description: "Array of recipient email addresses"
      },
      subject: { type: "string", description: "Email subject line" },
      body: { type: "string", description: "Email body content (HTML or plain text)" },
      cc: {
        type: "array",
        items: { type: "string" },
        description: "Array of CC recipients (optional)"
      },
      bcc: {
        type: "array",
        items: { type: "string" },
        description: "Array of BCC recipients (optional)"
      }
    },
    required: ["to", "subject", "body"]
  },
  handler: async ({ params }) => {
    // This function returns the draft email details without actually sending
    const draft = {
      to: params.to,
      subject: params.subject,
      body: params.body,
      cc: params.cc || [],
      bcc: params.bcc || [],
      status: "draft",
      timestamp: new Date().toISOString(),
      preview: `Would send email to: ${params.to.join(', ')}\nSubject: ${params.subject}\nBody: ${params.body.substring(0, 100)}...`
    };

    return draft;
  }
});

// Define the listEmails capability for reading emails (read-only)
server.capability("listEmails", {
  description: "List recent emails (read-only, for monitoring purposes)",
  inputSchema: {
    type: "object",
    properties: {
      folder: { type: "string", default: "INBOX", description: "Email folder to check" },
      limit: { type: "number", default: 10, description: "Number of emails to return" }
    }
  },
  handler: async ({ params }) => {
    // For now, return a mock response since actual email reading requires more complex IMAP setup
    return {
      success: false,
      error: "Email reading capability requires additional IMAP configuration",
      timestamp: new Date().toISOString(),
      info: "This server only supports sending emails. For reading, use the Gmail watcher script."
    };
  }
});

// Start the server
async function startServer() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.log("Email MCP Server running on stdio");
  } catch (error) {
    console.error("Failed to start Email MCP Server:", error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\nShutting down Email MCP Server...');
  await server.disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('Shutting down Email MCP Server...');
  await server.disconnect();
  process.exit(0);
});

startServer();