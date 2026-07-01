<div align="center">
  <img src="static/hombre_logo.jpg" alt="Hombre" width="400">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenCode](https://img.shields.io/badge/~%24_OpenCode-000000?style=for-the-badge&logo=terminal&logoColor=green)](https://opencode.ai)
[![MiMo](https://img.shields.io/badge/MiMo-FF6B35?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/XiaomiMiMo/MiMo-V2.5)

</div>

<p align="center">
  <img src="static/app_screenshot.png" alt="Hombre Dashboard" width="800">
</p>

## Why This Exists

Honcho is open source. You can run the server yourself. But the dashboard, the thing you actually interact with, is only available on their hosted platform. Self-host the server and you get an API endpoint and nothing else.

Hombre gives you a full web UI for workspaces, peers, sessions, chat, and configuration. Everything runs locally on your machine.

Built entirely with AI coding tools ([OpenCode](https://opencode.ai) + [MiMo](https://huggingface.co/XiaomiMiMo/MiMo-V2.5)). No shame about it.

## Features

- **Overview** — workspace stats, peer/session/conclusion counts at a glance
- **Peers** — list participants, view representations and peer cards, compare peers side-by-side
- **Sessions** — list conversations, view messages and summaries
- **Chat** — ask questions about a peer using natural language with streaming responses and typing indicator; adjustable reasoning depth
- **Conclusions** — browse and semantic search reasoning/memory with pagination and type filtering
- **Messages** — browse messages across all sessions with pagination
- **Settings** — configure LLM providers, embedding models, dialectic levels, and more
- **Workspace Merge** — merge two workspaces with conflict detection and resolution

### Additional Features

- **Soft Delete** — delete peers, messages, and conclusions (Honcho doesn't support native delete)
- **Export/Import** — export workspace data to portable JSON, import with conflict resolution
- **Notifications** — real-time notification bell for workspace events and new conclusions
- **Security** — role-based access control (admin/editor/viewer), rate limiting, audit logging
- **Typing Indicator** — animated dots while the model is thinking
- **Pagination** — load-more pattern for conclusions and messages
- **Supabase Integration** — optional Supabase support for auth, database storage, and real-time features

## Prerequisites

You need a running Honcho server. This dashboard is a frontend for it, it doesn't include the server itself.

- Honcho server running on `localhost:8000` (configurable via `HONCHO_URL`)
- See [honcho.dev](https://honcho.dev) for server setup instructions

## Quick Start

### Option 1: Python (System Install)

Requires Python 3.12+.

```bash
git clone https://github.com/lovethatbrandx/hombre.git
cd hombre
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the required environment variables:

```bash
export HONCHO_ENV_PATH=/path/to/honcho/.env
export HONCHO_COMPOSE_DIR=/path/to/honcho
```

Then run:

```bash
python app.py
```

Dashboard runs at `http://localhost:5000`.

### Option 2: Docker

The repo includes a `docker-compose.yml` ready to go. Edit the environment variables to match your setup:

```yaml
services:
  hombre:
    image: ghcr.io/lovethatbrandx/hombre/hombre:latest
    container_name: hombre
    ports:
      - "5000:5000"
    environment:
      - HONCHO_URL=http://host.docker.internal:8000
      - HONCHO_ENV_PATH=/path/to/honcho/.env    # <-- change this
      - HONCHO_COMPOSE_DIR=/path/to/honcho      # <-- and this
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

Then run:

```bash
docker compose up -d
```

To update:

```bash
docker compose pull
docker compose up -d
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HONCHO_URL` | No | `http://localhost:8000` | Honcho server URL |
| `HONCHO_API_KEY` | No | *(empty)* | API key for Honcho server authentication |
| `HONCHO_ENV_PATH` | No | *(empty)* | Path to Honcho `.env` file (for settings tab) |
| `HONCHO_COMPOSE_DIR` | No | *(empty)* | Docker Compose working directory for Honcho server |
| `DASHBOARD_USER` | No | *(empty)* | HTTP Basic Auth username (empty = no auth) |
| `DASHBOARD_PASSWORD` | No | *(empty)* | HTTP Basic Auth password (empty = no auth) |
| `DASHBOARD_ROLE` | No | `admin` | Role for single-user mode: `admin`, `editor`, or `viewer` |
| `DASHBOARD_USERS` | No | *(empty)* | Multi-user config: `user1:pass1:admin,user2:pass2:viewer` |
| `HOMBRE_LOG_DIR` | No | `logs` | Directory for access and audit logs |
| `SUPABASE_URL` | No | *(empty)* | Supabase project URL (enables Supabase integration) |
| `SUPABASE_KEY` | No | *(empty)* | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | No | *(empty)* | Supabase service role key (for admin operations) |

> **Note:** `HONCHO_ENV_PATH` and `HONCHO_COMPOSE_DIR` are optional. The app starts without them, but the Settings tab won't work until they're set.

## Settings Tab

The settings tab reads and writes the Honcho `.env` configuration file. Changes require a Docker container restart to take effect.

### Configurable Sections

- **LLM Provider** — API key
- **Embeddings** — model, base URL, transport, vector dimensions
- **Deriver** — background worker model config
- **Dialectic Levels** — minimal/low/medium/high/max reasoning levels
- **Summary** — summary generation model config
- **Dream** — deduction and induction model configs

### How It Works

1. Settings are read from the `.env` file at `HONCHO_ENV_PATH`
2. Edits are tracked client-side (dirty state with orange dot indicators)
3. "Save Changes" writes to `.env` (creates `.env.bak` backup)
4. "Apply & Restart" writes to `.env` and runs `docker compose up -d --force-recreate`
5. "Restore Backup" reverts to the previous `.env.bak`

## Security

- **Basic Auth** — Set `DASHBOARD_USER` and `DASHBOARD_PASSWORD` to enable HTTP Basic Auth. Without these, the dashboard is unauthenticated.
- **Supabase Auth** — Set `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_KEY` to enable Supabase authentication with email/password and magic links. Falls back to Basic Auth when not configured.
- **Role-Based Access** — Three roles: `admin` (full access), `editor` (create/edit/read), `viewer` (read-only). Configure via `DASHBOARD_ROLE` or `DASHBOARD_USERS`.
- **Rate Limiting** — In-memory sliding window rate limiter. Returns 429 with Retry-After header.
- **Audit Logging** — All settings changes logged to `logs/audit.log` with username and changed keys.
- **Request Logging** — All API requests logged to `logs/access.log` with timing and user info.
- **Bind address** — Binds to `0.0.0.0:5000` (all interfaces). Use a firewall or reverse proxy for production.
- **API key exposure** — The LLM API key is visible in the settings tab. Make sure the dashboard isn't publicly accessible.
- **Path traversal** — Proxy validates and URL-decodes paths before forwarding.
- **Security headers** — CSP, HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection.

## Project Structure

```
hombre/
├── app.py                      # FastAPI backend (auth, proxy, routes, pagination)
├── routes/
│   ├── __init__.py
│   ├── security.py             # Security middleware (RBAC, rate limiting, logging)
│   ├── settings.py             # Settings API (read/write .env, restart)
│   ├── deletes.py              # Soft-delete registry
│   ├── notifications.py        # Notification system
│   └── export.py               # Export/Import API
├── static/
│   ├── index.html              # SPA shell with notification bell
│   ├── style.css               # Dark theme CSS
│   ├── app.js                  # Frontend logic (all tabs, modal, notifications)
│   ├── icon.svg                # App icon
│   ├── hombre_logo.jpg         # Sidebar logo
│   └── app_screenshot.png      # Screenshot for README
├── docs/
│   ├── API.md                  # Complete API reference
│   ├── FEATURES.md             # Feature documentation
│   └── DEPLOYMENT.md           # Deployment guide
├── data/                       # Auto-created at runtime
│   ├── deleted.json            # Soft-deleted resource IDs
│   └── notifications.json      # Recent notifications
├── logs/                       # Auto-created at runtime
│   ├── access.log              # Request logs
│   └── audit.log               # Settings change logs
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## License

MIT
