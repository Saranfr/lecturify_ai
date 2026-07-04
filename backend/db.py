"""
Lecturify AI - Central Database Connection
Uses real MongoDB when available; falls back to mongomock for in-memory when MongoDB is unavailable.
"""
from typing import Optional, Any

_db: Optional[Any] = None
_using_mock = False

try:
    from backend.config import MONGODB_URI, MONGODB_DB
except ImportError:
    from config import MONGODB_URI, MONGODB_DB


def get_db():
    """Get MongoDB database. Uses real MongoDB if available; falls back to mongomock otherwise."""
    global _db, _using_mock
    if _db is not None:
        return _db

    # Try real MongoDB first (with short timeout)
    try:
        from pymongo import MongoClient
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        _db = client[MONGODB_DB]
        _using_mock = False
        print("[Lecturify] Connected to MongoDB")
        return _db
    except Exception as e:
        print(f"[Lecturify] MongoDB unavailable ({e}), using in-memory (mongomock)")

    # Fallback to mongomock
    try:
        import mongomock
        client = mongomock.MongoClient()
        _db = client[MONGODB_DB]
        _using_mock = True
        return _db
    except ImportError:
        print("[Lecturify] mongomock not installed. Run: pip install mongomock")
        return None


def is_using_mock() -> bool:
    """True if using in-memory mongomock (no MongoDB)."""
    return _using_mock
