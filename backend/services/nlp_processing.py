"""
Lecturify AI - NLP Concept Extraction
Sentence segmentation, keyword extraction, topic identification.
"""
import re
from typing import List, Dict, Optional

try:
    from backend.config import BLOOM_LEVELS
except ImportError:
    BLOOM_LEVELS = ["Remember", "Understand", "Apply"]

try:
    from backend.services.text_preprocessing import is_readable_text
except ImportError:
    from services.text_preprocessing import is_readable_text


def segment_sentences(text: str) -> List[str]:
    """Split text into sentences. Handles paragraphs, bullets, PPT-style content. Filters garbled text."""
    if not text or not text.strip():
        return []
    # Primary: split on sentence boundaries (min 12 chars for short bullets)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = [s.strip() for s in sentences if len(s.strip()) >= 12 and is_readable_text(s.strip())]
    if result:
        return result
    # Fallback: split on newlines (bullet points, PPT slides - min 12 chars)
    lines = [ln.strip() for ln in text.split('\n') if len(ln.strip()) >= 12 and is_readable_text(ln.strip())]
    if lines:
        return lines
    # Last resort: split on semicolons or double spaces (min 15 chars)
    chunks = re.split(r'[;]\s*|\s{2,}', text)
    return [c.strip() for c in chunks if len(c.strip()) >= 15 and is_readable_text(c.strip())]


def _is_ascii_word(w: str) -> bool:
    """Return True if word contains only ASCII letters (a-z, A-Z)."""
    return len(w) >= 3 and all(ord(c) < 128 and c.isalpha() for c in w)


def extract_keywords_spacy(text: str, top_n: int = 20) -> List[str]:
    """Extract keywords using spaCy (if available). ASCII-only to avoid garbled text."""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        doc = nlp(text[:10000])
        words = [t.lemma_ for t in doc if t.is_alpha and not t.is_stop and len(t) > 2]
        from collections import Counter
        filtered = [w for w, _ in Counter(words).most_common(top_n * 2) if _is_ascii_word(w)]
        return filtered[:top_n]
    except Exception:
        return extract_keywords_fallback(text, top_n)


def extract_keywords_nltk(text: str, top_n: int = 20) -> List[str]:
    """Extract keywords using NLTK (fallback). ASCII-only to avoid garbled text."""
    try:
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize
        stop = set(stopwords.words("english"))
        words = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in stop and len(w) > 2]
        from collections import Counter
        filtered = [w for w, _ in Counter(words).most_common(top_n * 2) if _is_ascii_word(w)]
        return filtered[:top_n]
    except Exception:
        return extract_keywords_fallback(text, top_n)


def extract_keywords_fallback(text: str, top_n: int = 20) -> List[str]:
    """Simple regex-based keyword extraction. ASCII a-zA-Z only - no garbled text."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stop = {"that", "this", "with", "from", "have", "been", "were", "when", "what", "which", "their", "there"}
    filtered = [w for w in words if w not in stop and _is_ascii_word(w)]
    from collections import Counter
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def extract_keywords(text: str, top_n: int = 20) -> List[str]:
    """Unified keyword extraction with fallbacks."""
    for fn in [extract_keywords_spacy, extract_keywords_nltk]:
        try:
            out = fn(text, top_n)
            if out:
                return out
        except Exception:
            continue
    return extract_keywords_fallback(text, top_n)


def identify_topics(text: str, top_k: int = 5) -> List[str]:
    """Identify main topics from text (uses top keywords as proxy)."""
    return extract_keywords(text, top_k)


def extract_concepts(text: str) -> Dict:
    """Full NLP extraction: sentences, keywords, topics."""
    sentences = segment_sentences(text)
    keywords = extract_keywords(text)
    topics = identify_topics(text)
    return {
        "sentences": sentences,
        "keywords": keywords,
        "topics": topics,
    }
