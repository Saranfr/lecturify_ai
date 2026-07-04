"""Lecture upload, processing, and management routes."""
import os
import uuid
import tempfile
from typing import Tuple, Optional, Dict


def _split_mcq_counts(total: int) -> Tuple[int, int, int]:
    """Split total into Easy, Medium, Hard (remainder goes to Easy, then Medium first)."""
    total = min(max(int(total), 10), 30)
    base = total // 3
    rem = total % 3
    easy = base + (1 if rem >= 1 else 0)
    medium = base + (1 if rem >= 2 else 0)
    hard = total - easy - medium
    return (easy, medium, hard)


def _count_mcqs_by_difficulty(mcqs: list) -> Dict[str, int]:
    out = {"easy": 0, "medium": 0, "hard": 0}
    for m in mcqs:
        d = (m.get("difficulty") or "Medium").strip().lower()
        if d == "easy":
            out["easy"] += 1
        elif d == "hard":
            out["hard"] += 1
        else:
            out["medium"] += 1
    return out
from flask import Blueprint, request, jsonify

try:
    from backend.config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, OUTPUT_FOLDER
    from backend.routes.auth_routes import optional_token_required
    from backend.services.stt_module import transcribe_audio, transcribe_video
    from backend.services.ocr_module import extract_text_from_image, extract_text_from_video_frames
    from backend.services.document_parser import extract_document_text
    from backend.services.nlp_processing import extract_concepts
    from backend.services.mcq_generator import generate_mcqs
    from backend.services.logging_service import log_event, create_notification
    from backend.services.text_preprocessing import sanitize_for_mcq
except ImportError:
    from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, OUTPUT_FOLDER
    from routes.auth_routes import optional_token_required
    from services.stt_module import transcribe_audio, transcribe_video
    from services.ocr_module import extract_text_from_image, extract_text_from_video_frames
    from services.document_parser import extract_document_text
    from services.nlp_processing import extract_concepts
    from services.mcq_generator import generate_mcqs
    from services.logging_service import log_event, create_notification
    from services.text_preprocessing import sanitize_for_mcq

lecture_bp = Blueprint("lecture", __name__)


def _topic_seed_content(topic: str) -> str:
    """Generate rich conceptual seed content from a topic name for MCQ generation."""
    t = topic.strip().title()
    return (
        f"{t} is a widely used technology and concept. "
        f"The main principles of {t} include: why {t} is important, how {t} works in practice, "
        f"key benefits and use cases of {t}, and how to apply {t} effectively. "
        f"Understanding the relationship between {t} and related concepts is essential. "
        f"Common applications involve using {t} for solving real-world problems. "
        f"Best practices for {t} emphasize reliability, scalability, and maintainability."
    )


def _get_video_diagnostic() -> str:
    """Return a short diagnostic about video processing deps."""
    try:
        from backend.services.stt_module import _get_ffmpeg_path
        ff = _get_ffmpeg_path()
        if ff and ff != "ffmpeg" and os.path.isfile(ff):
            return "imageio-ffmpeg OK. "
    except Exception:
        pass
    return "imageio-ffmpeg missing? "


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for exts in ALLOWED_EXTENSIONS.values():
        if ext in exts:
            return True
    return False


def _get_file_type(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


def _extract_text(file_path: str, file_type: str, original_filename: str = "") -> Tuple[str, Optional[str], Optional[str]]:
    """
    Extract text from uploaded file.
    For video: transcript first (primary), then OCR from frames as fallback/supplement.
    original_filename: user's filename (e.g. docker.mp4) for fallback when stored_path has UUID.
    Returns (text, error_message).
    """
    texts = []
    err_msg = None
    used_topic_fallback = None

    if file_type == "audio":
        t = transcribe_audio(file_path)
        if t and len(t.strip()) > 5:
            texts.append(t)
        elif not t:
            err_msg = "Audio transcription failed. Install: pip install imageio-ffmpeg openai-whisper. Ensure audio is audible."
    elif file_type == "video":
        temp_dir = tempfile.mkdtemp()
        display_name = (original_filename or os.path.basename(file_path)).strip()
        try:
            transcript = transcribe_video(file_path, temp_dir)
            if transcript and len(transcript.strip()) > 5:
                texts.append(transcript)
            ocr_text = extract_text_from_video_frames(
                file_path, frame_interval=8, max_frames=120, temp_dir=temp_dir
            )
            if ocr_text and len(ocr_text.strip()) > 5 and not ocr_text.startswith("["):
                ocr_lines = [ln.strip() for ln in ocr_text.split("\n") if len(ln.strip()) > 5]
                if ocr_lines:
                    texts.append("\n".join(ocr_lines[:60]))
            used_topic_fallback = None
            # Fallback: use original filename as topic when transcript + OCR both fail
            if not texts:
                topic = os.path.splitext(display_name)[0].replace("-", " ").replace("_", " ").strip()
                # Skip if topic looks like a UUID or hash (hex string)
                if len(topic) > 2 and not (len(topic) >= 20 and all(c in "0123456789abcdef" for c in topic.lower())):
                    seed = _topic_seed_content(topic)
                    texts.append(seed)
                    used_topic_fallback = topic
                    err_msg = None  # We have fallback content
                else:
                    diag = _get_video_diagnostic()
                    err_msg = (
                        "Video processing failed. " + diag +
                        " Video needs audible speech or readable slides. "
                        "Install all deps: python -m pip install imageio-ffmpeg openai-whisper moviepy av"
                    )
        finally:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
    elif file_type == "document":
        doc_text = extract_document_text(file_path)
        if doc_text and doc_text.strip().startswith("["):
            err_msg = doc_text.strip()
            if err_msg.startswith("[") and err_msg.endswith("]"):
                err_msg = err_msg[1:-1]
        else:
            texts.append(doc_text or "")
    elif file_type == "image":
        img_text = extract_text_from_image(file_path)
        if img_text and img_text.strip().startswith("["):
            err_msg = img_text.strip()
            if err_msg.startswith("[") and err_msg.endswith("]"):
                err_msg = err_msg[1:-1]
        else:
            texts.append(img_text or "")
    else:
        texts.append("")

    combined = "\n\n".join(t for t in texts if t and not (isinstance(t, str) and t.strip().startswith("[")))
    return (combined, err_msg, used_topic_fallback if file_type == "video" else None)


def _get_db():
    try:
        from backend.services.logging_service import get_db
        return get_db()
    except ImportError:
        from services.logging_service import get_db
        return get_db()


@lecture_bp.route("/upload", methods=["POST"])
@optional_token_required
def upload():
    """Upload lecture file (audio, video, PDF, DOCX, image, text)."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        f = request.files["file"]
        if not f or not f.filename:
            return jsonify({"error": "No filename"}), 400
        if not _allowed_file(f.filename):
            return jsonify({"error": "File type not allowed. Use: PDF, DOCX, PPTX, TXT, MP3, MP4, MPEG, PNG, JPG"}), 400

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        ext = f.filename.rsplit(".", 1)[-1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        path = os.path.abspath(os.path.join(UPLOAD_FOLDER, safe_name))
        f.save(path)

        user_id = getattr(request, "user_id", "anonymous")
        lecture_id = str(uuid.uuid4())
        from datetime import datetime

        db = _get_db()
        if db is None:
            return jsonify({"error": "Database unavailable. Ensure MongoDB is running on localhost:27017"}), 503

        db.lectures.insert_one({
            "_id": lecture_id,
            "filename": f.filename,
            "stored_path": path,
            "file_type": _get_file_type(f.filename),
            "user_id": user_id,
            "status": "uploaded",
            "created_at": datetime.utcnow().isoformat(),
        })
        try:
            log_event("upload", user_id=user_id, lecture_id=lecture_id, details={"filename": f.filename})
            if user_id != "anonymous":
                create_notification(
                    user_id,
                    "upload",
                    "Lecture Uploaded",
                    f"{f.filename} uploaded. Click to process and generate MCQs.",
                    link=f"/lectures/{lecture_id}",
                    lecture_id=lecture_id,
                )
        except Exception:
            pass

        return jsonify({
            "lecture_id": lecture_id,
            "filename": f.filename,
            "status": "uploaded",
        }), 201
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@lecture_bp.route("/process/<lecture_id>", methods=["POST"])
@optional_token_required
def process(lecture_id):
    """Run full pipeline: extract text -> NLP -> MCQ generation."""
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    lecture = db.lectures.find_one({"_id": lecture_id})
    if not lecture:
        return jsonify({"error": "Lecture not found"}), 404

    path = lecture.get("stored_path")
    if not path or not os.path.isfile(path):
        return jsonify({"error": "File not found on disk"}), 404

    try:
        file_type = lecture.get("file_type", "document")
        filename = lecture.get("filename", "")
        text, extract_err, topic_fallback = _extract_text(path, file_type, original_filename=filename)
        min_chars = 10 if file_type in ("audio", "video") else 20
        if not text or len(text.strip()) < min_chars:
            err = extract_err or "Insufficient text extracted"
            db.lectures.update_one(
                {"_id": lecture_id},
                {"$set": {"status": "failed", "error": err}}
            )
            return jsonify({"error": err}), 400

        text = sanitize_for_mcq(
            text,
            filename=filename,
            from_audio_video=file_type in ("audio", "video"),
        )
        min_after = 10 if file_type in ("audio", "video") else 20
        if len(text.strip()) < min_after:
            db.lectures.update_one(
                {"_id": lecture_id},
                {"$set": {"status": "failed", "error": "Insufficient content after cleanup"}}
            )
            return jsonify({"error": "Insufficient content after cleanup"}), 400

        concepts = extract_concepts(text)
        num_q = 18
        if request.is_json and request.json:
            num_q = int(request.json.get("num_questions", 18))
        num_q = min(max(num_q, 10), 30)
        ne, nm, nh = _split_mcq_counts(num_q)
        mcqs = generate_mcqs(
            text,
            num_easy=ne,
            num_medium=nm,
            num_hard=nh,
            from_audio_video=file_type in ("audio", "video"),
            topic_fallback=topic_fallback,
        )

        db.lectures.update_one(
            {"_id": lecture_id},
            {
                "$set": {
                    "status": "processed",
                    "transcript": text[:5000],
                    "concepts": concepts,
                    "mcqs": mcqs,
                    "processed_at": __import__("datetime").datetime.utcnow().isoformat(),
                }
            },
        )

        user_id = getattr(request, "user_id", "anonymous")
        log_event("processing", user_id=user_id, lecture_id=lecture_id, details={"mcq_count": len(mcqs)})
        if user_id != "anonymous":
            create_notification(
                user_id,
                "processing_complete",
                "MCQs Generated",
                f"Generated {len(mcqs)} MCQs from {filename}",
                link=f"/lectures/{lecture_id}",
                lecture_id=lecture_id,
            )

        by_diff = _count_mcqs_by_difficulty(mcqs)
        return jsonify({
            "lecture_id": lecture_id,
            "status": "processed",
            "transcript_preview": text[:500],
            "mcq_count": len(mcqs),
            "mcqs": mcqs,
            "requested_total": num_q,
            "mcq_by_difficulty": by_diff,
        })
    except Exception as e:
        db.lectures.update_one(
            {"_id": lecture_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return jsonify({"error": str(e)}), 500


@lecture_bp.route("/lectures", methods=["GET"])
@optional_token_required
def list_lectures():
    """List lectures for current user."""
    db = _get_db()
    if db is None:
        return jsonify([])

    user_id = getattr(request, "user_id", None)
    q = {"user_id": user_id} if user_id else {}
    lectures = list(db.lectures.find(q).sort("created_at", -1).limit(100))
    for l in lectures:
        l["id"] = str(l.pop("_id", ""))
    return jsonify(lectures)


@lecture_bp.route("/lectures/<lecture_id>", methods=["GET"])
@optional_token_required
def get_lecture(lecture_id):
    """Get single lecture with MCQs."""
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    lecture = db.lectures.find_one({"_id": lecture_id})
    if not lecture:
        return jsonify({"error": "Not found"}), 404

    lecture["id"] = str(lecture.pop("_id", ""))
    return jsonify(lecture)


@lecture_bp.route("/lectures/<lecture_id>", methods=["DELETE"])
@optional_token_required
def delete_lecture(lecture_id):
    """Delete a lecture and its stored file."""
    db = _get_db()
    if db is None:
        return jsonify({"error": "Database unavailable"}), 503

    lecture = db.lectures.find_one({"_id": lecture_id})
    if not lecture:
        return jsonify({"error": "Lecture not found"}), 404

    path = lecture.get("stored_path")
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as e:
            print(f"[Lecturify] Could not delete file {path}: {e}")

    db.lectures.delete_one({"_id": lecture_id})

    user_id = getattr(request, "user_id", "anonymous")
    try:
        log_event("delete", user_id=user_id, lecture_id=lecture_id, details={"filename": lecture.get("filename", "")})
    except Exception:
        pass

    return jsonify({"message": "Lecture deleted"}), 200
