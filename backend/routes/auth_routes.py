"""JWT authentication and role-based access routes."""
from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
from datetime import datetime, timedelta

try:
    from backend.config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, MONGODB_URI, MONGODB_DB
except ImportError:
    from config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES, MONGODB_URI, MONGODB_DB

auth_bp = Blueprint("auth", __name__)

# Limited demo accounts (checked before MongoDB). Stable user_id strings for JWT.
HARDCODE_ACCOUNTS = [
    {
        "id": "hc-instructor",
        "email": "instructor@lecturify.demo",
        "password": "Lect2026!",
        "role": "Instructor",
        "name": "Demo Instructor",
    },
    {
        "id": "hc-student",
        "email": "student@lecturify.demo",
        "password": "Stud2026!",
        "role": "Student",
        "name": "Demo Student",
    },
    {
        "id": "hc-admin",
        "email": "admin@lecturify.demo",
        "password": "Admin2026!",
        "role": "Admin",
        "name": "Demo Admin",
    },
]


def get_db():
    try:
        from backend.db import get_db as _get_db
        return _get_db()
    except ImportError:
        try:
            from db import get_db as _get_db
            return _get_db()
        except ImportError:
            return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            return jsonify({"error": "Token required"}), 401
        try:
            payload = jwt.decode(
                token.split()[1], JWT_SECRET_KEY, algorithms=["HS256"]
            )
            request.user_id = payload.get("user_id")
            request.user_role = payload.get("role", "Instructor")
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated


def optional_token_required(f):
    """Allow access without token; set user_id='anonymous' when no token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            try:
                payload = jwt.decode(
                    token.split()[1], JWT_SECRET_KEY, algorithms=["HS256"]
                )
                request.user_id = payload.get("user_id")
                request.user_role = payload.get("role", "Instructor")
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                request.user_id = "anonymous"
                request.user_role = "Instructor"
        else:
            request.user_id = "anonymous"
            request.user_role = "Instructor"
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if getattr(request, "user_role", "") != "Admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "Instructor")
    name = data.get("name", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    if role not in ("Instructor", "Admin", "Student"):
        role = "Instructor"

    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    if db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 400

    import bcrypt
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    user = {
        "email": email,
        "password": hashed,
        "role": role,
        "name": name or email.split("@")[0],
        "created_at": datetime.utcnow().isoformat(),
    }
    db.users.insert_one(user)
    return jsonify({"message": "Registered", "email": email}), 201


def _jwt_for_builtin(user_id: str, email: str, role: str, name: str) -> dict:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return {
        "token": token,
        "user": {"email": email, "role": role, "name": name},
    }


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    email_lower = email.lower()
    for acct in HARDCODE_ACCOUNTS:
        if acct["email"].lower() == email_lower and acct["password"] == password:
            return jsonify(_jwt_for_builtin(acct["id"], acct["email"], acct["role"], acct["name"]))

    db = get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    import bcrypt
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"error": "Invalid credentials"}), 401

    payload = {
        "user_id": str(user["_id"]),
        "email": email,
        "role": user.get("role", "Instructor"),
        "exp": datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return jsonify({
        "token": token,
        "user": {"email": email, "role": user.get("role"), "name": user.get("name", "")},
    })


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    return jsonify({
        "user_id": request.user_id,
        "role": request.user_role,
    })
