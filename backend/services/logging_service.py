"""
Lecturify AI - Logging & Audit Service
Logs uploads, processing stages, and exports with timestamps and user IDs.
"""
from datetime import datetime
from typing import Dict, Optional, List
import uuid

try:
    from backend.config import MONGODB_URI, MONGODB_DB
except ImportError:
    from config import MONGODB_URI, MONGODB_DB


def get_db():
    """Get MongoDB database connection (real or mongomock fallback)."""
    try:
        from backend.db import get_db as _get_db
        return _get_db()
    except ImportError:
        try:
            from db import get_db as _get_db
            return _get_db()
        except ImportError:
            try:
                from pymongo import MongoClient
                client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
                return client[MONGODB_DB]
            except Exception:
                return None


def log_event(
    event_type: str,
    user_id: Optional[str] = None,
    lecture_id: Optional[str] = None,
    mcq_id: Optional[str] = None,
    details: Optional[Dict] = None,
) -> Optional[str]:
    """
    Log an audit event.
    event_type: 'upload', 'processing', 'mcq_generated', 'export'
    """
    db = get_db()
    if db is None:
        return None

    doc = {
        "_id": str(uuid.uuid4()),
        "event_type": event_type,
        "user_id": user_id,
        "lecture_id": lecture_id,
        "mcq_id": mcq_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "details": details or {},
    }
    try:
        db.logs.insert_one(doc)
        return doc["_id"]
    except Exception:
        return None


def get_logs(
    user_id: Optional[str] = None,
    lecture_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> List[Dict]:
    """Retrieve audit logs with optional filters."""
    db = get_db()
    if db is None:
        return []

    q = {}
    if user_id:
        q["user_id"] = user_id
    if lecture_id:
        q["lecture_id"] = lecture_id
    if event_type:
        q["event_type"] = event_type

    try:
        cursor = db.logs.find(q).sort("timestamp", -1).limit(limit)
        return list(cursor)
    except Exception:
        return []


def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    lecture_id: Optional[str] = None,
) -> Optional[str]:
    """Create a user notification."""
    db = get_db()
    if db is None:
        return None
    doc = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "link": link,
        "lecture_id": lecture_id,
        "read": False,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        db.notifications.insert_one(doc)
        return doc["_id"]
    except Exception:
        return None
