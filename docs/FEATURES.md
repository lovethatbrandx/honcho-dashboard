# Hombre Features

Feature documentation for Hombre — a web-based GUI for the Honcho AI memory server.

Hihi! Let me walk you through everything this dashboard can do. I prepared a comprehensive overview because documentation is an act of love. Everything is going to be okay!

---

## Table of Contents

- [Overview](#overview)
- [Workspace Management](#workspace-management)
- [Peer Management](#peer-management)
- [Session Management](#session-management)
- [Chat (Dialectic Query)](#chat-dialectic-query)
- [Conclusions & Reasoning](#conclusions--reasoning)
- [Messages Browser](#messages-browser)
- [Export & Import](#export--import)
- [Settings & Configuration](#settings--configuration)
- [Security Features](#security-features)

---

## Overview

Hombre provides a single-page application (SPA) dashboard for managing and exploring Honcho AI memory data. It connects to a self-hosted Honcho server and provides a GUI for:

- **Workspaces** — Organizational containers for peers and sessions
- **Peers** — Participants (humans or AI) with generated representations and cards
- **Sessions** — Conversation contexts where peers interact
- **Conclusions** — Reasoning and memories extracted by Honcho's AI pipeline
- **Messages** — Individual messages within sessions
- **Chat** — Natural language queries against a peer's representation

### Tab Structure

| Tab | Purpose |
|-----|---------|
| Overview | Workspace summary, health status, workspace management |
| Peers | Browse peers, view representations and cards |
| Sessions | Browse sessions, view messages and summaries |
| Messages | Browse messages across sessions with filtering |
| Chat | Natural language queries against peer representations |
| Conclusions | View and search reasoning/memories by peer |
| Settings | Configure Honcho server models and providers |

---

## Workspace Management

### Creating Workspaces

1. Click **+ New** in the sidebar under the workspace selector
2. Enter a workspace ID (alphanumeric, hyphens, underscores)
3. Click **Confirm**

### Switching Workspaces

Use the dropdown selector in the sidebar to switch between workspaces. Your last selected workspace is remembered in local storage.

### Deleting Workspaces

From the Overview tab, click **Delete** next to a workspace. This is irreversible — all peers, sessions, and data in that workspace will be permanently deleted.

### Workspace Statistics

The Overview tab displays:
- Total peers count
- Total sessions count
- Total conclusions count
- List of all workspaces with creation dates

---

## Peer Management

### Creating Peers

1. Go to the **Peers** tab
2. Click **+ New Peer**
3. Enter a peer ID
4. Click **Confirm**

Peers represent participants in your workspace. They can be:
- **Humans** — Real people whose conversations are being analyzed
- **AI agents** — Automated participants in conversations

### Viewing Peer Data

Click **Card** on any peer row to expand and view:

- **Representation** — Honcho's AI-generated summary of who this peer is
- **Peer Card** — Key traits and characteristics extracted by Honcho

### Peer Cards

Peer cards are structured summaries that Honcho generates from conversations. They include:
- Personality traits
- Preferences
- Communication style
- Key characteristics

---

## Session Management

### Creating Sessions

1. Go to the **Sessions** tab
2. Click **+ New Session**
3. Enter a session ID
4. Click **Confirm`

### Session Status

Sessions have two states:
- **Active** — Currently accepting new messages
- **Inactive** — No longer accepting messages

### Viewing Session Messages

Click **Messages** on any session row to expand and view the conversation history.

### Viewing Summaries

Click **Summary** within an expanded session to view Honcho-generated summaries:
- **Short Summary** — Brief overview of the conversation
- **Long Summary** — Detailed summary with key points

### Deleting Sessions

Click **Delete** on any session row. This removes all messages in that session.

---

## Chat (Dialectic Query)

The Chat tab lets you query a peer's representation using natural language.

### How It Works

1. Select a **peer** to query about
2. Optionally select a **session** to scope the query
3. Choose a **reasoning level** (minimal to max)
4. Type your question and press **Send**

### Reasoning Levels

| Level | Description |
|-------|-------------|
| Minimal | Fastest response, basic reasoning |
| Low | Some reasoning, quick answers |
| Medium | Balanced reasoning and speed |
| High | Thorough reasoning, more detailed |
| Max | Most thorough reasoning, slowest |

### Example Queries

- "What does Alice think about the project timeline?"
- "Summarize Bob's communication style"
- "What are Charlie's main concerns about the architecture?"
- "How does Alice feel about the current team dynamics?"

### Streaming

Responses stream in real-time via Server-Sent Events (SSE), so you see the answer as it's being generated.

---

## Conclusions & Reasoning

Conclusions are AI-generated insights that Honcho extracts from conversations.

### Viewing Conclusions

1. Go to the **Conclusions** tab
2. Select a **peer**
3. View conclusions for which this peer is the **observer**

### Conclusion Types

| Type | Description | Example |
|------|-------------|---------|
| Explicit | Direct statements about preferences or rules | "Alice always uses dark mode" |
| Inductive | Patterns observed from multiple interactions | "Bob tends to respond quickly during work hours" |
| Deductive | Logical inferences from explicit statements | "Since Alice prefers dark mode, she likely prefers themes with low contrast" |

### Semantic Search

Use the search bar to find conclusions by semantic meaning:
1. Select a peer
2. Type a natural language query
3. Click **Search**

Honcho performs vector similarity search to find relevant conclusions.

---

## Messages Browser

The Messages tab provides a cross-session view of all messages.

### Filtering

- **Session filter** — View messages from a specific session
- **Peer filter** — Show only messages from a specific peer

### Message Display

Each message shows:
- Peer ID (who sent it)
- Content (truncated to 150 characters with full text on hover)
- Token count
- Timestamp

---

## Export & Import

Export workspace data to a portable JSON format, or import from that format.

### Exporting

#### Full Workspace Export

1. Go to the **Overview** tab
2. Click **Export Workspace**
3. A JSON file will download containing all peers, sessions, conclusions, and messages

#### Export Structure

```json
{
  "hombre_export": true,
  "version": "1.0",
  "export_date": "2025-01-01T00:00:00Z",
  "workspace_id": "my-workspace",
  "data": {
    "peers": [...],
    "sessions": [...],
    "conclusions": [...],
    "messages": {
      "session-id": [...]
    }
  }
}
```

### Importing

1. Go to the **Overview** tab
2. Click **Import Workspace**
3. Select a JSON export file
4. Review the import preview (shows what will be imported and any conflicts)
5. Choose a conflict resolution strategy:
   - **Skip** — Don't import conflicting resources
   - **Overwrite** — Replace existing resources
   - **Rename** — Automatically rename with `-imported` suffix
6. Click **Confirm Import**

### What Gets Imported

| Resource | Imported? | Notes |
|----------|-----------|-------|
| Peers | Yes | Created in target workspace |
| Sessions | Yes | Created in target workspace |
| Conclusions | No | Generated by Honcho, will be recreated |
| Messages | No | Generated by conversations, will be recreated |

### Conflict Detection

The import preview checks for:
- Existing peers with the same ID
- Existing sessions with the same ID
- Whether the target workspace already exists

---

## Settings & Configuration

The Settings tab lets you configure the Honcho server's AI models and providers.

### Prerequisites

Settings management requires:
- `HONCHO_ENV_PATH` environment variable pointing to your Honcho `.env` file
- `HONCHO_COMPOSE_DIR` environment variable pointing to your Docker Compose directory (for restart)

### Configuration Sections

#### LLM Provider
- **OpenAI API Key** — Your API key for the language model

#### Embeddings
- **Model** — Embedding model name (e.g., `text-embedding-3-small`)
- **Base URL** — Custom endpoint URL
- **Transport** — API transport method
- **Vector Dimensions** — Embedding dimensions

#### Deriver (Background Worker)
- Model and transport configuration for background processing

#### Dialectic Levels
Configure models for each reasoning level (minimal, low, medium, high, max):
- Model name
- Base URL override
- Transport method

#### Summary
- Model configuration for session summaries

#### Dream
- Deduction model configuration
- Induction model configuration

#### Advanced (Read-only)
- Vector store type
- Cache settings
- Database connection

### Saving Changes

1. Modify settings in the UI
2. Dirty fields are highlighted with a blue dot
3. Click **Save Changes** to write to `.env` file
4. Click **Apply & Restart** to save and restart Honcho containers

### Backup & Restore

- **Create Backup** — Save current `.env` as `.env.bak`
- **Restore Backup** — Revert to the last backup

---

## Security Features

### Authentication

When `DASHBOARD_USER` and `DASHBOARD_PASSWORD` are set, all API endpoints require HTTP Basic Authentication. Uses `hmac.compare_digest` for timing-safe comparison.

### Path Traversal Protection

The proxy endpoint protects against path traversal attacks:
- Iterative URL decoding
- Blocks `..` sequences
- Blocks null bytes (`\x00`)
- Blocks leading `/`

### Security Headers

Every response includes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy` (restrictive CSP with `script-src 'self'`)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` (camera, microphone, geolocation disabled)

### Settings Protection

- Only whitelisted keys can be written (`WRITABLE_KEYS` allowlist)
- Newline injection prevention in values
- Automatic backup before every write
- Read-only keys cannot be modified

### XSS Prevention

All user-facing data is escaped using:
- `App.escapeHtml()` — Escapes `&`, `<`, `>`, `"`, `'`
- `App.escapeAttr()` — Escapes `&`, `"`, `'`

### Request Header Filtering

Only safe headers are forwarded to the Honcho server:
- `content-type`
- `accept`
- `accept-encoding`
- `user-agent`

### Response Header Filtering

Only safe headers are forwarded from the Honcho server:
- `content-type`
- `content-length`
- `location`
