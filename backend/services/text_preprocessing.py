"""
Lecturify AI - Text Preprocessing for MCQ Generation
Sanitizes extracted text: removes filename/path artifacts, cleans audio/video transcripts.
"""
import re
from typing import Optional


# File extensions and path patterns to strip
FILE_EXT_PATTERN = re.compile(
    r'\b[\w\-]+\.[a-z0-9]{2,5}\b', re.IGNORECASE
)  # doc.pdf, lecture_01.mp4
PATH_LIKE_PATTERN = re.compile(
    r'[A-Za-z]:\\[^\s]+|/(?:usr|home|tmp|var|mnt)/[^\s]*|\.{1,2}/[^\s]*'
)
# Common transcript artifacts (avoid removing valid parentheticals)
TRANSCRIPT_ARTIFACTS = [
    r'\[[\w\s]+\]',  # [inaudible], [music], [laughter]
    r'\(in(?:audible|audable)\)',  # (inaudible)
    r'\(background\s+\w+\)',  # (background noise)
    r'\b(um|uh|er|ah|hmm)\b',  # filler words
]
TRANSCRIPT_CLEAN_PATTERN = re.compile('|'.join(TRANSCRIPT_ARTIFACTS), re.IGNORECASE)
# Repeated words/phrases (2+ times)
REPEATED_WORDS = re.compile(r'\b(\w{3,})\s+(\1\s+)+', re.IGNORECASE)
# Conceptual sentence starters (prioritize these for MCQ)
CONCEPTUAL_MARKERS = [
    'because', 'therefore', 'thus', 'hence', 'so', 'causes', 'caused by',
    'explain', 'explains', 'means', 'implies', 'reason', 'result',
    'how does', 'why does', 'what causes', 'what is the', 'relationship',
    'compare', 'contrast', 'difference between', 'similar to', 'unlike',
    'principle', 'concept', 'theory', 'law', 'rule', 'process',
]


def remove_filename_artifacts(text: str, filename: Optional[str] = None) -> str:
    """Remove path and file.extension patterns. Avoid removing filename base (may be valid content)."""
    if not text:
        return text
    # Remove path-like strings
    text = PATH_LIKE_PATTERN.sub(' ', text)
    # Remove explicit file.extension patterns (e.g. document.pdf, video.mp4)
    text = FILE_EXT_PATTERN.sub(' ', text)
    # Collapse multiple spaces
    return re.sub(r'\s+', ' ', text).strip()


def clean_transcript(text: str) -> str:
    """Clean audio/video transcript artifacts."""
    if not text:
        return text
    # Remove [brackets] and (parens) content
    text = TRANSCRIPT_CLEAN_PATTERN.sub(' ', text)
    # Fix repeated words
    text = REPEATED_WORDS.sub(r'\1 ', text)
    # Remove timestamps like [00:01:23] or 00:01:23
    text = re.sub(r'\[\d{1,2}:\d{2}(?::\d{2})?\]|\d{1,2}:\d{2}(?::\d{2})?\s*', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def is_readable_text(s: str, min_ratio: float = 0.6) -> bool:
    """
    Return True if text is mostly readable ASCII (English + punctuation).
    Filters symbol font, garbled Unicode, CJK, and other non-Latin scripts.
    """
    if not s or len(s.strip()) < 3:
        return False
    s = s.strip()
    # Only ASCII (0-127): a-z A-Z 0-9 and common punctuation - blocks 湏猭牣敥
    punctuation = " .,;:'\"-?!()/%\n\t"
    readable = sum(1 for c in s if ord(c) < 128 and (c.isalnum() or c in punctuation))
    return readable / len(s) >= min_ratio


def _remove_garbled_lines(text: str) -> str:
    """Remove lines that are mostly non-printable or symbol/garbled Unicode."""
    lines = [ln.strip() for ln in text.split("\n") if is_readable_text(ln)]
    return "\n".join(lines)


def remove_non_ascii_runs(text: str) -> str:
    """Remove contiguous non-ASCII character runs (symbol font, CJK, garbled). Keeps English content."""
    if not text:
        return text
    # Replace runs of non-ASCII chars with a space, then collapse spaces
    result = re.sub(r"[^\x20-\x7e]+", " ", text)
    return re.sub(r"\s+", " ", result).strip()


def sanitize_for_mcq(
    text: str,
    filename: Optional[str] = None,
    from_audio_video: bool = False,
) -> str:
    """
    Full sanitization before MCQ generation.
    Removes filename/path artifacts, garbled text, and optionally cleans transcript.
    """
    if not text or len(text.strip()) < 20:
        return text
    text = remove_non_ascii_runs(text)  # Strip symbol font, CJK, garbled runs first
    text = _remove_garbled_lines(text)
    text = remove_filename_artifacts(text, filename)
    if from_audio_video:
        text = clean_transcript(text)
    return re.sub(r'\s+', ' ', text).strip()


def is_conceptual_sentence(sentence: str) -> bool:
    """Return True if sentence contains conceptual/logic indicators."""
    lower = sentence.lower()
    return any(marker in lower for marker in CONCEPTUAL_MARKERS)


def score_sentence_for_conceptual(sentence: str) -> float:
    """Higher = more conceptual. Used to rank sentences for MCQ generation."""
    score = 0.0
    lower = sentence.lower()
    for marker in CONCEPTUAL_MARKERS:
        if marker in lower:
            score += 1.0
    # Prefer longer explanatory sentences (50-200 chars)
    length = len(sentence)
    if 50 <= length <= 200:
        score += 0.5
    elif 200 < length <= 400:
        score += 0.3
    return score
