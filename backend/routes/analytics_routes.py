"""Dashboard & analytics routes."""
from collections import Counter
from flask import Blueprint, jsonify, request

try:
    from backend.services.logging_service import get_db, create_notification
    from backend.services.dataset_loader import get_dataset_info
    from backend.routes.auth_routes import token_required, optional_token_required
except ImportError:
    from services.logging_service import get_db, create_notification
    from services.dataset_loader import get_dataset_info
    from routes.auth_routes import token_required, optional_token_required

analytics_bp = Blueprint("analytics", __name__)


def _empty_overview(difficulty_filter: str = "All"):
    """Return empty dashboard structure when DB unavailable."""
    info = get_dataset_info()
    return {
        "lectures_total": 0,
        "lectures_by_status": {},
        "bloom_distribution": {},
        "total_mcqs": 0,
        "pending_review": 0,
        "dataset_info": info,
        "difficulty_filter": difficulty_filter,
    }


@analytics_bp.route("/analytics/overview", methods=["GET"])
def overview():
    """Lecture processing status, Bloom distribution, topic coverage.
    Query param ?difficulty=Easy|Medium|Hard filters stats to MCQs of that level only."""
    db = get_db()
    if db is None:
        return jsonify(_empty_overview())

    difficulty_filter = request.args.get("difficulty", "All")
    if difficulty_filter not in ("All", "Easy", "Medium", "Hard"):
        difficulty_filter = "All"

    try:
        lectures = list(db.lectures.find({}))
        bloom_counts = Counter()
        status_counts = Counter()
        total_mcqs = 0
        lectures_with_level = 0

        for lec in lectures:
            mcqs = lec.get("mcqs", [])
            if difficulty_filter != "All":
                mcqs = [m for m in mcqs if m.get("difficulty") == difficulty_filter]
            if not mcqs and difficulty_filter != "All":
                continue
            if mcqs:
                lectures_with_level += 1
            status_counts[lec.get("status", "unknown")] += 1
            for m in mcqs:
                total_mcqs += 1
                bloom_counts[m.get("bloom_level", "Unknown")] += 1

        dataset_info = get_dataset_info()
        return jsonify({
            "lectures_total": lectures_with_level if difficulty_filter != "All" else len(lectures),
            "lectures_by_status": dict(status_counts),
            "bloom_distribution": dict(bloom_counts),
            "total_mcqs": total_mcqs,
            "pending_review": 0,
            "dataset_info": dataset_info,
            "difficulty_filter": difficulty_filter,
        })
    except Exception:
        return jsonify(_empty_overview())


@analytics_bp.route("/analytics/logs", methods=["GET"])
def logs():
    """Recent audit logs."""
    db = get_db()
    if db is None:
        return jsonify([])
    try:
        limit = int(request.args.get("limit", 50))
        cursor = db.logs.find({}).sort("timestamp", -1).limit(limit)
        items = list(cursor)
        for x in items:
            x["id"] = str(x.pop("_id", ""))
        return jsonify(items)
    except Exception:
        return jsonify([])


@analytics_bp.route("/notifications", methods=["GET"])
@optional_token_required
def get_notifications():
    """Get user notifications (unread first)."""
    db = get_db()
    if db is None:
        return jsonify([])
    user_id = getattr(request, "user_id", "anonymous")
    limit = int(request.args.get("limit", 20))
    cursor = db.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    items = []
    for x in cursor:
        x["id"] = str(x.pop("_id", ""))
        items.append(x)
    return jsonify(items)


@analytics_bp.route("/notifications/<nid>/read", methods=["POST"])
@optional_token_required
def mark_notification_read(nid):
    """Mark notification as read."""
    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503
    user_id = getattr(request, "user_id", "anonymous")
    r = db.notifications.update_one({"_id": nid, "user_id": user_id}, {"$set": {"read": True}})
    return jsonify({"status": "ok" if r.modified_count else "not_found"})


@analytics_bp.route("/datasets/info", methods=["GET"])
def dataset_info():
    """Dataset availability and training readiness."""
    info = get_dataset_info()
    return jsonify(info)
