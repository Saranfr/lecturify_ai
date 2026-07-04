"""Export MCQs to PDF, JSON, CSV."""
import os
import json
import csv
from flask import Blueprint, request, jsonify, send_file

try:
    from backend.config import OUTPUT_FOLDER
    from backend.services.logging_service import get_db, log_event
    from backend.routes.auth_routes import optional_token_required
except ImportError:
    from config import OUTPUT_FOLDER
    from services.logging_service import get_db, log_event
    from routes.auth_routes import optional_token_required

export_bp = Blueprint("export", __name__)


def _get_mcqs_for_export(lecture_id: str):
    """Return all MCQs for the lecture."""
    db = get_db()
    if db is None:
        return []
    lecture = db.lectures.find_one({"_id": lecture_id})
    if not lecture:
        return []
    return lecture.get("mcqs", [])


@export_bp.route("/json/<lecture_id>", methods=["GET"])
@optional_token_required
def export_json(lecture_id):
    """Export MCQs as JSON."""
    mcqs = _get_mcqs_for_export(lecture_id)
    if not mcqs:
        return jsonify({"error": "No MCQs"}), 400

    output = {"lecture_id": lecture_id, "mcqs": mcqs}
    path = os.path.join(OUTPUT_FOLDER, f"{lecture_id}_mcqs.json")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log_event("export", lecture_id=lecture_id, details={"format": "json", "count": len(mcqs)})
    return send_file(path, as_attachment=True, download_name=f"lecturify_{lecture_id}.json")


@export_bp.route("/csv/<lecture_id>", methods=["GET"])
@optional_token_required
def export_csv(lecture_id):
    """Export MCQs as CSV."""
    mcqs = _get_mcqs_for_export(lecture_id)
    if not mcqs:
        return jsonify({"error": "No MCQs"}), 400

    path = os.path.join(OUTPUT_FOLDER, f"{lecture_id}_mcqs.csv")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question", "option_1", "option_2", "option_3", "option_4", "correct_answer", "explanation", "bloom_level"])
        for m in mcqs:
            opts = m.get("options", [])[:4]
            while len(opts) < 4:
                opts.append("")
            writer.writerow([
                m.get("question", ""),
                opts[0], opts[1], opts[2], opts[3],
                m.get("correct_answer", ""),
                m.get("explanation", ""),
                m.get("bloom_level", ""),
            ])

    log_event("export", lecture_id=lecture_id, details={"format": "csv", "count": len(mcqs)})
    return send_file(path, as_attachment=True, download_name=f"lecturify_{lecture_id}.csv")


@export_bp.route("/pdf/<lecture_id>", methods=["GET"])
@optional_token_required
def export_pdf(lecture_id):
    """Export MCQs as PDF."""
    mcqs = _get_mcqs_for_export(lecture_id)
    if not mcqs:
        return jsonify({"error": "No MCQs"}), 400

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
    except ImportError:
        return jsonify({"error": "Install reportlab: pip install reportlab"}), 500

    path = os.path.join(OUTPUT_FOLDER, f"{lecture_id}_mcqs.pdf")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = [Paragraph("Lecturify AI - MCQ Export", styles["Title"])]

    for i, m in enumerate(mcqs, 1):
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"<b>Q{i}. {m.get('question', '')}</b>", styles["Normal"]))
        for j, opt in enumerate(m.get("options", [])[:4], 1):
            story.append(Paragraph(f"   {chr(64+j)}. {opt}", styles["Normal"]))
        story.append(Paragraph(f"<b>Answer:</b> {m.get('correct_answer', '')}", styles["Normal"]))
        story.append(Paragraph(f"<b>Bloom:</b> {m.get('bloom_level', '')}", styles["Normal"]))
        if m.get("explanation"):
            story.append(Paragraph(f"<i>Explanation: {m['explanation'][:300]}...</i>", styles["Normal"]))

    doc.build(story)
    log_event("export", lecture_id=lecture_id, details={"format": "pdf", "count": len(mcqs)})
    return send_file(path, as_attachment=True, download_name=f"lecturify_{lecture_id}.pdf")


def _escape_xml(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")


@export_bp.route("/lms/<lecture_id>", methods=["GET"])
@optional_token_required
def export_lms(lecture_id):
    """Export MCQs as Moodle XML (LMS-ready format)."""
    mcqs = _get_mcqs_for_export(lecture_id)
    if not mcqs:
        return jsonify({"error": "No MCQs"}), 400

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<quiz>"]
    for i, m in enumerate(mcqs):
        qtext = _escape_xml(m.get("question", ""))
        lines.append('  <question type="multichoice">')
        lines.append("    <name><text><![CDATA[Q" + str(i + 1) + "]]></text></name>")
        lines.append('    <questiontext format="html"><text><![CDATA[<p>' + qtext + "</p>]]></text></questiontext>")
        lines.append("    <defaultgrade>1</defaultgrade>")
        lines.append("    <single>true</single>")
        answers = m.get("options", [])[:4]
        correct = m.get("correct_answer", "")
        for opt in answers:
            frac = "100" if opt == correct else "0"
            lines.append('    <answer fraction="' + frac + '"><text><![CDATA[' + _escape_xml(opt) + "]]></text></answer>")
        lines.append("  </question>")
    lines.append("</quiz>")
    path = os.path.join(OUTPUT_FOLDER, f"{lecture_id}_lms.xml")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    log_event("export", lecture_id=lecture_id, details={"format": "lms", "count": len(mcqs)})
    return send_file(path, as_attachment=True, download_name=f"lecturify_{lecture_id}_moodle.xml", mimetype="application/xml")
