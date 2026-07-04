"""
Lecturify AI - OCR Module
Extracts text from images using OpenCV + pytesseract.
"""
import os
from typing import List, Optional

try:
    from backend.config import UPLOAD_FOLDER
except ImportError:
    UPLOAD_FOLDER = "."


def extract_text_from_image(image_path: str) -> str:
    """Extract text from a single image using pytesseract."""
    try:
        import cv2
        import pytesseract
    except ImportError:
        return "[Install opencv-python and pytesseract. Also install Tesseract OCR.]"

    if not os.path.isfile(image_path):
        return ""

    img = cv2.imread(image_path)
    if img is None:
        return ""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip()


def extract_text_from_video_frames(
    video_path: str,
    frame_interval: int = 30,
    max_frames: int = 50,
    temp_dir: str = "",
) -> str:
    """Extract text from video by sampling frames and running OCR."""
    try:
        import cv2
        import pytesseract
    except ImportError:
        return "[opencv-python and pytesseract required]"

    if not os.path.isfile(video_path):
        return ""

    cap = cv2.VideoCapture(video_path)
    texts = []
    frame_idx = 0
    count = 0

    while count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            t = pytesseract.image_to_string(gray).strip()
            if t and len(t) > 6:
                texts.append(t)
                count += 1
        frame_idx += 1

    cap.release()
    return "\n".join(texts) if texts else ""
