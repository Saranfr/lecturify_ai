"""
Lecturify AI - Flask Application
Three-tier: Presentation (React) <-> Application (Flask API) <-> Data & AI
"""
import importlib
import os
import sys

# Ensure backend is on path when run from project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

try:
    from backend.config import SECRET_KEY
except ImportError:
    from config import SECRET_KEY

from backend.routes.auth_routes import auth_bp
from backend.routes.lecture_routes import lecture_bp
from backend.routes.export_routes import export_bp
from backend.routes.analytics_routes import analytics_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
    CORS(app, origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174", "http://localhost:3000"])

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(lecture_bp, url_prefix="/api/lecture")
    app.register_blueprint(export_bp, url_prefix="/api/export")
    app.register_blueprint(analytics_bp, url_prefix="/api")

    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "Lecturify AI"}

    @app.route("/api/diagnostic/video")
    def video_diagnostic():
        """Check video processing dependencies. Use this to debug upload failures."""
        out = {"ok": True, "checks": {}}
        try:
            from backend.services.stt_module import _get_ffmpeg_path
            ff = _get_ffmpeg_path()
            out["checks"]["ffmpeg"] = "OK (" + str(ff)[:80] + ")" if ff else "NOT FOUND"
            if not ff or ff == "ffmpeg":
                out["ok"] = False
        except Exception as e:
            out["checks"]["ffmpeg"] = f"Error: {e}"
            out["ok"] = False
        try:
            # Dynamic load: package is openai-whisper; avoids static-analysis "cannot resolve whisper"
            importlib.import_module("whisper")
            out["checks"]["whisper"] = "OK"
        except ImportError:
            out["checks"]["whisper"] = "NOT INSTALLED - run: pip install openai-whisper"
            out["ok"] = False
        try:
            import imageio_ffmpeg
            out["checks"]["imageio_ffmpeg"] = "OK"
        except ImportError:
            out["checks"]["imageio_ffmpeg"] = "NOT INSTALLED - run: pip install imageio-ffmpeg"
            out["ok"] = False
        import sys
        out["python"] = sys.executable
        return out

    @app.errorhandler(500)
    def handle_500(e):
        return {"error": str(e) if str(e) else "Internal server error"}, 500

    return app


app = create_app()


def _seed_default_user():
    """Create default instructor if no users exist (real MongoDB or mongomock)."""
    try:
        import bcrypt
        from backend.db import get_db
    except ImportError:
        return
    try:
        db = get_db()
        if db is None:
            return
        if db.users.count_documents({}) == 0:
            hashed = bcrypt.hashpw(b"Test@123", bcrypt.gensalt()).decode("utf-8")
            db.users.insert_one({
                "email": "instructor@lecturify.com",
                "password": hashed,
                "role": "Instructor",
                "name": "Instructor",
                "created_at": __import__("datetime").datetime.utcnow().isoformat(),
            })
            print("[Lecturify] Default user created: instructor@lecturify.com / Test@123")
    except Exception:
        pass


_seed_default_user()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
