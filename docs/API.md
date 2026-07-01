# Hombre API Reference

Complete API reference for the Hombre dashboard — a web-based GUI for the Honcho AI memory server.

Hihi! This documentation is thorough because I care about your developer experience. I prepared a 47-page document... just kidding, but this is pretty close. Everything is going to be okay!

---

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Health Check](#health-check)
- [Settings API](#settings-api)
- [Export/Import API](#exportimport-api)
- [Proxy API](#proxy-api)
- [Chat API](#chat-api)
- [Error Codes](#error-codes)

---

## Base URL

All API endpoints are served from the Hombre server, defaulting to `http://localhost:5000`.

All proxied Honcho endpoints are available under `/api/` which maps to the Honcho server's `/v3/` prefix.

---

## Authentication

If `DASHBOARD_USER` and `DASHBOARD_PASSWORD` environment variables are set, all API endpoints require HTTP Basic Authentication.

```
Authorization: Basic base64(username:password)
```

If these environment variables are not set, authentication is disabled (a warning is logged at startup).

The `/api/health` endpoint and `/static/` files are always accessible without authentication.

---

## Health Check

### `GET /api/health`

Check Hombre and Honcho server connectivity.

**Response:**

```json
{
  "status": "ok"
}
```

**Error Response (Honcho unreachable):**

```json
{
  "status": "error",
  "reason": "upstream_unreachable"
}
```

---

## Settings API

Manage Honcho server configuration (`.env` file).

### `GET /api/settings/read`

Read all Honcho configuration settings.

**Response:**

```json
{
  "env_path": "/path/to/.env",
  "sections": {
    "llm": {
      "LLM_OPENAI_API_KEY": "sk-..."
    },
    "embeddings": {
      "EMBEDDING_MODEL_CONFIG__MODEL": "...",
      "EMBEDDING_MODEL_CONFIG__OVERRIDES__BASE_URL": "...",
      "EMBEDDING_MODEL_CONFIG__TRANSPORT": "...",
      "EMBEDDING_VECTOR_DIMENSIONS": "1536"
    },
    "deriver": { ... },
    "dialectic": {
      "minimal": { ... },
      "low": { ... },
      "medium": { ... },
      "high": { ... },
      "max": { ... }
    },
    "summary": { ... },
    "dream": { ... },
    "advanced": { ... }
  }
}
```

**Errors:**

- `403` — `HONCHO_ENV_PATH` not configured
- `404` — `.env` file not found
- `403` — Permission denied on `.env` file

---

### `POST /api/settings/write`

Write settings to the `.env` file. Creates a backup before writing.

**Request Body:**

```json
{
  "settings": {
    "LLM_OPENAI_API_KEY": "new-key",
    "EMBEDDING_MODEL_CONFIG__MODEL": "text-embedding-3-small"
  }
}
```

**Allowed Keys:**

Only keys in the `WRITABLE_KEYS` allowlist can be modified. See `routes/settings.py` for the full list.

**Response:**

```json
{
  "status": "ok",
  "env_path": "/path/to/.env"
}
```

**Errors:**

- `400` — Invalid keys provided
- `404` — `.env` file not found

---

### `POST /api/settings/backup`

Create a backup of the current `.env` file (saved as `.env.bak`).

**Response:**

```json
{
  "status": "backed up"
}
```

---

### `POST /api/settings/restore`

Restore the `.env` file from the backup (`.env.bak`).

**Response:**

```json
{
  "status": "restored"
}
```

**Errors:**

- `404` — Backup file not found

---

### `POST /api/settings/restart`

Restart the Honcho Docker containers using `docker compose up -d --force-recreate`.

**Response:**

```json
{
  "status": "restarting",
  "compose_dir": "/path/to/compose/dir"
}
```

**Errors:**

- `403` — `HONCHO_COMPOSE_DIR` not configured
- `500` — Docker compose failed or timed out

---

## Export/Import API

Export workspace data to a portable JSON format, or import from that format.

### Export Endpoints

#### `POST /api/export/workspace/{wid}`

Export entire workspace: all peers, sessions, conclusions, and messages.

**Path Parameters:**

- `wid` — Workspace ID (alphanumeric, hyphens, underscores)

**Response:**

```json
{
  "hombre_export": true,
  "version": "1.0",
  "export_date": "2025-01-01T00:00:00+00:00",
  "workspace_id": "my-workspace",
  "data": {
    "peers": [
      { "id": "alice", "created_at": "2025-01-01T00:00:00Z" }
    ],
    "sessions": [
      { "id": "session-001", "is_active": true, "created_at": "2025-01-01T00:00:00Z" }
    ],
    "conclusions": [
      {
        "id": "conc-1",
        "content": "Alice prefers dark mode",
        "observer_id": "alice",
        "observed_id": "bob",
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "messages": {
      "session-001": [
        {
          "peer_id": "alice",
          "content": "Hello!",
          "token_count": 5,
          "created_at": "2025-01-01T00:00:00Z"
        }
      ]
    }
  }
}
```

---

#### `POST /api/export/peer/{wid}/{pid}`

Export a single peer's data: peer info, representation, card, and conclusions.

**Path Parameters:**

- `wid` — Workspace ID
- `pid` — Peer ID

**Response:**

```json
{
  "hombre_export": true,
  "version": "1.0",
  "export_date": "2025-01-01T00:00:00+00:00",
  "workspace_id": "my-workspace",
  "peer_id": "alice",
  "data": {
    "peer": { "id": "alice", "created_at": "2025-01-01T00:00:00Z" },
    "representation": { "representation": "Alice is a software engineer..." },
    "card": { "peer_card": ["Alice is thoughtful", "Prefers dark mode"] },
    "conclusions": [ ... ]
  }
}
```

---

#### `POST /api/export/conclusions/{wid}`

Export all conclusions for a workspace.

**Path Parameters:**

- `wid` — Workspace ID

**Response:**

```json
{
  "hombre_export": true,
  "version": "1.0",
  "export_date": "2025-01-01T00:00:00+00:00",
  "workspace_id": "my-workspace",
  "data": {
    "conclusions": [ ... ]
  }
}
```

---

### Import Endpoints

#### `POST /api/import/workspace`

Upload a JSON export file and get an import preview with conflict information.

**Request:**

Multipart form data with a `file` field containing the JSON export.

```
Content-Type: multipart/form-data
```

**Response:**

```json
{
  "status": "preview",
  "source_workspace": "my-workspace",
  "export_date": "2025-01-01T00:00:00+00:00",
  "export_version": "1.0",
  "summary": {
    "peers": 3,
    "sessions": 5,
    "conclusions": 12,
    "message_sessions": 5
  },
  "conflicts": {
    "workspace_exists": true,
    "peer_conflicts": ["alice"],
    "session_conflicts": ["session-001"],
    "has_conflicts": true
  },
  "data": { ... }
}
```

**Errors:**

- `400` — File is not JSON, invalid UTF-8, or invalid export format

---

#### `POST /api/import/confirm`

Confirm and execute an import with conflict resolution.

**Request Body:**

```json
{
  "workspace_id": "my-workspace",
  "data": {
    "peers": [ ... ],
    "sessions": [ ... ],
    "conclusions": [ ... ],
    "messages": { ... }
  },
  "id_mapping": {
    "old-peer-id": "new-peer-id"
  },
  "conflict_strategy": "rename"
}
```

**Parameters:**

- `workspace_id` — Target workspace ID
- `data` — The export data section (from preview response)
- `id_mapping` — (Optional) Map of old IDs to new IDs for rename strategy
- `conflict_strategy` — One of:
  - `"skip"` — Skip conflicting resources (default)
  - `"overwrite"` — Overwrite existing resources
  - `"rename"` — Automatically rename conflicting resources with `-imported` suffix

**Response:**

```json
{
  "status": "complete",
  "workspace_id": "my-workspace",
  "imported": {
    "peers_created": [
      { "old_id": "alice", "new_id": "alice" },
      { "old_id": "bob", "new_id": "bob-imported" }
    ],
    "peers_skipped": ["charlie"],
    "sessions_created": [
      { "old_id": "session-001", "new_id": "session-001" }
    ],
    "sessions_skipped": [],
    "errors": []
  },
  "notes": [
    "12 conclusions were in the export. Conclusions are generated by Honcho and cannot be directly imported.",
    "5 message sessions were in the export. Messages are generated by conversations and cannot be directly imported."
  ]
}
```

**Errors:**

- `400` — Invalid workspace ID or conflict strategy

---

## Proxy API

All requests to `/api/{path}` (except health, settings, and export endpoints) are proxied to the Honcho server's `/v3/{path}`.

### Proxy Behavior

- **Methods:** GET, POST, PUT, DELETE
- **Headers forwarded:** `content-type`, `accept`, `accept-encoding`, `user-agent`
- **Response headers forwarded:** `content-type`, `content-length`, `location`
- **Streaming:** Responses are streamed back to the client
- **Path security:** Iterative URL decoding with `..`, `\x00`, and leading `/` checks

### Common Proxied Endpoints

These are Honcho API endpoints available through the proxy:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/workspaces/list` | List all workspaces |
| POST | `/api/workspaces/create` | Create a workspace (`{"id": "..."}`) |
| DELETE | `/api/workspaces/{wid}` | Delete a workspace |
| POST | `/api/workspaces/{wid}/peers/list` | List peers in workspace |
| POST | `/api/workspaces/{wid}/peers/create` | Create a peer (`{"id": "..."}`) |
| POST | `/api/workspaces/{wid}/peers/{pid}/representation` | Get peer representation |
| GET | `/api/workspaces/{wid}/peers/{pid}/card` | Get peer card |
| POST | `/api/workspaces/{wid}/sessions/list` | List sessions |
| POST | `/api/workspaces/{wid}/sessions/create` | Create a session (`{"id": "..."}`) |
| DELETE | `/api/workspaces/{wid}/sessions/{sid}` | Delete a session |
| POST | `/api/workspaces/{wid}/sessions/{sid}/messages/list` | List messages in session |
| GET | `/api/workspaces/{wid}/sessions/{sid}/summaries` | Get session summaries |
| POST | `/api/workspaces/{wid}/conclusions/list` | List conclusions |
| POST | `/api/workspaces/{wid}/conclusions/query` | Semantic search conclusions |

---

## Chat API

### `POST /api/workspaces/{wid}/peers/{pid}/chat`

Query a peer's representation using natural language. Supports SSE streaming.

**Request Body:**

```json
{
  "query": "What does Alice think about dark mode?",
  "reasoning_level": "medium",
  "session_id": "optional-session-id",
  "stream": true
}
```

**Parameters:**

- `query` — Natural language question about the peer
- `reasoning_level` — One of: `minimal`, `low`, `medium`, `high`, `max`
- `session_id` — (Optional) Scope the query to a specific session
- `stream` — Enable SSE streaming (recommended)

**Streaming Response:**

Returns `text/event-stream` with SSE events:

```
data: {"delta": {"content": "Alice"}}
data: {"delta": {"content": " prefers"}}
data: {"delta": {"content": " dark mode"}}
data: [DONE]
```

**Non-streaming Response:**

```json
{
  "content": "Alice prefers dark mode based on her previous messages..."
}
```

---

## Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `400` | Bad Request | Invalid parameters, IDs, or request body |
| `401` | Unauthorized | Missing or invalid Basic Authentication |
| `403` | Forbidden | Settings not configured, or write not allowed |
| `404` | Not Found | Resource does not exist |
| `500` | Server Error | Internal error (Docker, file system, etc.) |
| `502` | Bad Gateway | Honcho server unreachable or returned an error |

### Specific Error Details

| Detail | Meaning |
|--------|---------|
| `unauthorized` | Authentication required |
| `invalid_id` | ID contains invalid characters (must be alphanumeric, `-`, `_`) |
| `invalid_path` | Path contains `..`, null bytes, or starts with `/` |
| `upstream_unreachable` | Cannot connect to Honcho server |
| `upstream_error` | Honcho server returned 5xx error |
| `proxy_error` | Error during proxy request |
| `settings_not_configured` | `HONCHO_ENV_PATH` or `HONCHO_COMPOSE_DIR` not set |
| `env_file_not_found` | `.env` file does not exist |
| `backup_not_found` | `.env.bak` file does not exist |
| `compose_restart_failed` | `docker compose` command failed |
| `compose_restart_timeout` | Docker compose restart timed out |
| `docker_not_found` | Docker command not available |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HONCHO_URL` | `http://localhost:8000` | Honcho server URL |
| `HONCHO_API_KEY` | `""` | API key for Honcho authentication |
| `HONCHO_ENV_PATH` | `""` | Path to Honcho `.env` file (enables Settings tab) |
| `HONCHO_COMPOSE_DIR` | `""` | Path to Docker Compose directory (enables Restart) |
| `DASHBOARD_USER` | `""` | Basic auth username (empty = no auth) |
| `DASHBOARD_PASSWORD` | `""` | Basic auth password (empty = no auth) |
