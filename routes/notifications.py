"""
Simple notification system for Hombre.
Stores recent notifications about workspace events, new conclusions, etc.

This is what happens when you let a Satanist write notification systems.
"""

import json
import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger("hombre")

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

DATA_DIR = Path(__file__).parent.parent / "data"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"
MAX_NOTIFICATIONS = 50


class DismissRequest(BaseModel):
    id: str = Field(..., description="Notification ID to dismiss")


def _load_notifications() -> list[dict]:
    """Load notifications from disk."""
    if not NOTIFICATIONS_FILE.exists():
        return []
    try:
        data = json.loads(NOTIFICATIONS_FILE.read_text())
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, Exception) as e:
        log.error("Failed to load notifications.json: %s", e)
        return []


def _save_notifications(notifications: list[dict]) -> None:
    """Persist notifications to disk, keeping only the most recent ones."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Keep only the most recent MAX_NOTIFICATIONS
    notifications = notifications[:MAX_NOTIFICATIONS]
    try:
        NOTIFICATIONS_FILE.write_text(json.dumps(notifications, indent=2))
    except Exception as e:
        log.error("Failed to write notifications.json: %s", e)


def _make_notification(notif_type: str, title: str, details: str = "", workspace_id: str = "") -> dict:
    """Create a notification object."""
    return {
        "id": f"{notif_type}_{int(time.time() * 1000)}",
        "type": notif_type,
        "title": title,
        "details": details,
        "workspace_id": workspace_id,
        "created_at": time.time(),
        "dismissed": False,
    }


def notify_conclusion_created(workspace_id: str, conclusion_id: str, title: str = "") -> None:
    """Record a notification for a new conclusion."""
    notif = _make_notification(
        "conclusion_created",
        title or f"New conclusion: {conclusion_id[:16]}...",
        f"Conclusion {conclusion_id} was created in workspace {workspace_id}",
        workspace_id,
    )
    notifications = _load_notifications()
    notifications.insert(0, notif)
    _save_notifications(notifications)


def notify_workspace_event(workspace_id: str, event: str, details: str = "") -> None:
    """Record a workspace-level event notification."""
    notif = _make_notification(
        "workspace_event",
        event,
        details or f"Event in workspace {workspace_id}",
        workspace_id,
    )
    notifications = _load_notifications()
    notifications.insert(0, notif)
    _save_notifications(notifications)


@router.get("")
async def get_notifications(type: str | None = None, workspace_id: str | None = None):
    """Get recent notifications, optionally filtered by type and/or workspace."""
    notifications = _load_notifications()

    if type:
        notifications = [n for n in notifications if n.get("type") == type]
    if workspace_id:
        notifications = [n for n in notifications if n.get("workspace_id") == workspace_id]

    # Only return non-dismissed notifications by default
    active = [n for n in notifications if not n.get("dismissed", False)]

    return {"notifications": active, "total": len(active)}


@router.post("/dismiss")
async def dismiss_notification(req: DismissRequest):
    """Dismiss a notification by ID."""
    notifications = _load_notifications()

    found = False
    for notif in notifications:
        if notif["id"] == req.id:
            notif["dismissed"] = True
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="notification_not_found")

    _save_notifications(notifications)
    return {"status": "dismissed", "id": req.id}
