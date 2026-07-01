# Hombre Deployment Guide

Deployment guide for Hombre — a web-based GUI for the Honcho AI memory server.

Just wanted to remind you that following these steps carefully will save you debugging time later. I prepared this guide with love. Everything is going to be okay!

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Environment Variables](#environment-variables)
- [Honcho Server Requirements](#honcho-server-requirements)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Python 3.12+** — Backend runtime
- **Docker & Docker Compose** — For running the Honcho server
- **Honcho Server** — The AI memory server (runs on port 8000 by default)

---

## Local Development

### 1. Clone the Repository

```bash
git clone <repository-url>
cd hombre
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

- `fastapi==0.138.0` — Web framework
- `uvicorn[standard]==0.49.0` — ASGI server
- `httpx==0.28.1` — Async HTTP client (for Honcho proxy)

### 4. Set Environment Variables

```bash
export HONCHO_URL=http://localhost:8000
export HONCHO_API_KEY=your-api-key  # optional
export HONCHO_ENV_PATH=/path/to/honcho/.env  # enables Settings tab
export HONCHO_COMPOSE_DIR=/path/to/honcho/docker  # enables Restart
export DASHBOARD_USER=admin  # optional
export DASHBOARD_PASSWORD=secret  # optional
```

### 5. Start the Honcho Server

```bash
# In a separate terminal
cd /path/to/honcho/docker
docker compose up -d
```

### 6. Start Hombre

```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### 7. Open the Dashboard

Navigate to `http://localhost:5000` in your browser.

### Syntax Check Commands

```bash
# Python
python3 -m py_compile app.py
python3 -m py_compile routes/settings.py
python3 -m py_compile routes/export.py

# JavaScript
node --check static/app.js
```

---

## Docker Deployment

### 1. Build the Docker Image

```bash
docker compose build
```

### 2. Configure Environment Variables

Edit `docker-compose.yml` or create a `.env` file:

```env
HONCHO_URL=http://honcho:8000
HONCHO_API_KEY=
HONCHO_ENV_PATH=/config/.env
HONCHO_COMPOSE_DIR=/compose
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=secret
```

### 3. Start the Services

```bash
docker compose up -d
```

### 4. Verify Health

```bash
curl http://localhost:5000/api/health
```

### Docker Compose Reference

```yaml
services:
  dashboard:
    build: .
    ports:
      - "5000:5000"
    environment:
      - HONCHO_URL=http://honcho:8000
      - HONCHO_API_KEY=${HONCHO_API_KEY}
      - DASHBOARD_USER=${DASHBOARD_USER}
      - DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
```

---

## Environment Variables

### Required

None — Hombre will start with minimal functionality.

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `HONCHO_URL` | `http://localhost:8000` | Honcho server URL. Use `http://honcho:8000` in Docker. |
| `HONCHO_API_KEY` | `""` | API key for Honcho authentication. Set if your Honcho server requires it. |
| `HONCHO_ENV_PATH` | `""` | Path to Honcho's `.env` file. Enables the Settings tab for configuration management. |
| `HONCHO_COMPOSE_DIR` | `""` | Path to the Docker Compose directory for the Honcho server. Enables the Restart button. |
| `DASHBOARD_USER` | `""` | Username for Basic Authentication. Empty = no auth (startup warning logged). |
| `DASHBOARD_PASSWORD` | `""` | Password for Basic Authentication. Empty = no auth (startup warning logged). |

### Variable Details

#### `HONCHO_URL`

The URL where your Honcho server is accessible. 

- **Local development:** `http://localhost:8000`
- **Docker Compose:** `http://honcho:8000` (use the service name)
- **Remote server:** `https://your-honcho-server.com`

#### `HONCHO_API_KEY`

If your Honcho server uses API key authentication, set this variable. Hombre will include it as a `Bearer` token in all requests to Honcho.

#### `HONCHO_ENV_PATH`

Absolute path to the Honcho server's `.env` configuration file. This enables:

- **Reading** all Honcho configuration in the Settings tab
- **Writing** model settings directly from the dashboard
- **Backup/restore** of configuration
- **Apply & Restart** to apply changes

Example: `/opt/honcho/.env` or `/home/user/honcho/config/.env`

#### `HONCHO_COMPOSE_DIR`

Absolute path to the directory containing the Honcho server's `docker-compose.yml`. This enables the **Restart** button in Settings.

Example: `/opt/honcho/docker` or `/home/user/honcho`

#### `DASHBOARD_USER` / `DASHBOARD_PASSWORD`

When both are set, all API endpoints require HTTP Basic Authentication. The dashboard will prompt for credentials in the browser.

**Security Note:** Both values must be set together. If only one is set, authentication is disabled with a warning.

---

## Honcho Server Requirements

### Running Honcho

Hombre expects a Honcho server running and accessible at `HONCHO_URL`. The Honcho server should be:

- Running on the configured URL
- Health endpoint accessible at `/health`
- API accessible at `/v3/`

### Honcho API Version

Hombre proxies requests to Honcho's `/v3/` API. Ensure your Honcho server supports this version.

### Network Configuration

If running in Docker, ensure:

1. Hombre can reach the Honcho container
2. The Honcho server is on the same Docker network
3. Use Docker service names for `HONCHO_URL` (e.g., `http://honcho:8000`)

### Ports

| Service | Default Port | Description |
|---------|-------------|-------------|
| Hombre | 5000 | Dashboard web interface |
| Honcho | 8000 | AI memory server |

---

## Troubleshooting

### Dashboard Shows "Unreachable"

**Symptom:** Health dot is red, text says "Unreachable"

**Solutions:**
1. Verify Honcho server is running: `curl http://localhost:8000/health`
2. Check `HONCHO_URL` matches your Honcho server location
3. If using Docker, ensure both services are on the same network

### Settings Tab Shows 403

**Symptom:** Settings tab shows "Configuration not found"

**Solutions:**
1. Set `HONCHO_ENV_PATH` to the correct path
2. Verify the file exists and is readable
3. Check file permissions

### Restart Button Returns 500

**Symptom:** Clicking "Apply & Restart" fails

**Solutions:**
1. Set `HONCHO_COMPOSE_DIR` to the correct path
2. Verify Docker is installed and running
3. Check that the Honcho server's compose file is in the directory

### Authentication Loop

**Symptom:** Browser keeps prompting for credentials

**Solutions:**
1. Ensure both `DASHBOARD_USER` and `DASHBOARD_PASSWORD` are set
2. Clear browser cache
3. Check for typos in credentials

### Export Fails

**Symptom:** Export returns 502 or error

**Solutions:**
1. Verify Honcho server is running
2. Check the workspace ID is valid
3. Look at Hombre logs for specific error messages

### Import Validation Fails

**Symptom:** Import preview shows "invalid_export_format"

**Solutions:**
1. Ensure the file is valid JSON
2. Check the file was exported from Hombre (has `hombre_export: true`)
3. Verify all required fields are present (`version`, `export_date`, `workspace_id`, `data`)

---

## Development Tips

### Hot Reload

The `--reload` flag watches for file changes and restarts automatically:

```bash
python3 -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Logging

Hombre uses Python's built-in logging. To increase verbosity:

```bash
LOG_LEVEL=DEBUG python3 -m uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

### Debugging

To debug the proxy, check the Hombre logs. Upstream errors are logged with:

```
WARNING: Upstream error 500 on POST workspaces/my-ws/sessions/list
```

### Testing the API

```bash
# Health check
curl http://localhost:5000/api/health

# List workspaces
curl -X POST http://localhost:5000/api/workspaces/list \
  -H "Content-Type: application/json" \
  -d '{}'

# Export workspace
curl -X POST http://localhost:5000/api/export/workspace/my-ws \
  -o export.json

# Import workspace
curl -X POST http://localhost:5000/api/import/workspace \
  -F "file=@export.json"
```
