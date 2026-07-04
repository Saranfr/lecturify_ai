"""
Lecturify AI - MCQ Generator
Generates conceptual and logic-based MCQs from text.
Filters out filename/path-based questions. Supports Easy, Medium, Hard.
"""
import os
import re
import random
from typing import List, Dict, Optional

try:
    from backend.config import MODELS_FOLDER, BLOOM_LEVELS
except ImportError:
    from config import MODELS_FOLDER, BLOOM_LEVELS

from .bloom_classifier import classify_bloom

try:
    from backend.services.text_preprocessing import is_readable_text
except ImportError:
    from services.text_preprocessing import is_readable_text

DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]

# Patterns that indicate filename/path/unwanted content
FILENAME_EXT_PATTERN = re.compile(r'\b\w+\.(pdf|docx|doc|mp3|mp4|wav|m4a|jpg|jpeg|png|txt)\b', re.IGNORECASE)
# UUID/hash in question (long hex string)
UUID_LIKE_PATTERN = re.compile(r'\b[0-9a-f]{20,}\b', re.IGNORECASE)
CONCEPTUAL_STARTERS = (
    'because', 'therefore', 'thus', 'hence', 'explain', 'means', 'implies',
    'how does', 'why does', 'what causes', 'relationship', 'principle',
    'concept', 'theory', 'compare', 'contrast', 'difference', 'process',
    'enables', 'allows', 'ensures', 'critical', 'essential', 'key to',
    'depends on', 'leads to', 'results in', 'provides', 'supports',
)


def _is_filename_based(mcq: Dict) -> bool:
    """Return True only if question/options clearly reference filenames (word.pdf, etc)."""
    combined = f"{mcq.get('question', '')} {' '.join(mcq.get('options', []))}"
    return bool(FILENAME_EXT_PATTERN.search(combined))


def _contains_uuid_or_bad(mcq: Dict) -> bool:
    """Filter out MCQs with UUIDs, hashes, or fill-in-blank with UUID-like answers."""
    q = mcq.get("question", "")
    opts = " ".join(mcq.get("options", []))
    if UUID_LIKE_PATTERN.search(q) or UUID_LIKE_PATTERN.search(opts):
        return True
    if "Fill in the blank:" in q and "______" in q:
        correct = mcq.get("correct_answer", "")
        if UUID_LIKE_PATTERN.search(correct) or len(correct) > 30:
            return True
    return False


def _contains_garbled_text(mcq: Dict) -> bool:
    """Return True if question or options contain non-ASCII/garbled text."""
    q = mcq.get("question", "")
    opts = " ".join(mcq.get("options", []))
    combined = f"{q} {opts}"
    return not is_readable_text(combined, min_ratio=0.85)


def _generate_topic_conceptual_mcqs(topic: str, num_questions: int = 9) -> List[Dict]:
    """Generate conceptual MCQs from a topic name (e.g. Docker, Python). Skips garbled topics."""
    t = topic.strip().title()
    if not t or not is_readable_text(t):
        return []
    templates = [
        {
            "question": f"Why is {t} considered important in modern development?",
            "options": [f"Enables efficient resource isolation and portability", "It is a programming language", "Replaces all other tools", "Only used in small projects"],
            "explanation": f"{t} provides key benefits for development and deployment.",
            "bloom_level": "Understand",
            "difficulty": "Medium",
        },
        {
            "question": f"What is a key principle behind how {t} works?",
            "options": [f"Abstraction and encapsulation of environments", "Requires manual configuration", "Works only on specific operating systems", "Limited to single-machine use"],
            "explanation": f"{t} relies on abstraction to simplify workflows.",
            "bloom_level": "Understand",
            "difficulty": "Medium",
        },
        {
            "question": f"Which best describes a common use case for {t}?",
            "options": [f"Deploying and scaling applications consistently", "Writing documentation only", "Replacing databases", "Managing user accounts"],
            "explanation": f"{t} is widely used for deployment and scaling.",
            "bloom_level": "Apply",
            "difficulty": "Medium",
        },
        {
            "question": f"What relationship does {t} have with related technologies?",
            "options": [f"Integrates with ecosystem tools for orchestration", "Operates in complete isolation", "Replaces all related tools", "Has no integration points"],
            "explanation": f"{t} works alongside complementary technologies.",
            "bloom_level": "Understand",
            "difficulty": "Hard",
        },
        {
            "question": f"What does 'best practices' for {t} typically emphasize?",
            "options": [f"Reliability, security, and maintainability", "Using the latest version only", "Minimal documentation", "Single-user access"],
            "explanation": f"{t} best practices focus on production readiness.",
            "bloom_level": "Remember",
            "difficulty": "Easy",
        },
        {
            "question": f"How does {t} help solve real-world problems?",
            "options": [f"By providing consistent, repeatable environments", "By eliminating the need for testing", "By reducing code complexity alone", "By replacing cloud services"],
            "explanation": f"{t} addresses deployment and environment challenges.",
            "bloom_level": "Apply",
            "difficulty": "Medium",
        },
        {
            "question": f"What distinguishes {t} from traditional approaches?",
            "options": [f"Portability and reproducibility across environments", "Requires more manual setup", "Only supports legacy systems", "Cannot scale horizontally"],
            "explanation": f"{t} offers advantages over traditional methods.",
            "bloom_level": "Understand",
            "difficulty": "Hard",
        },
        {
            "question": f"Which concept is essential to understand {t}?",
            "options": [f"The relationship between {t} and its components", "Memorizing command syntax only", "Ignoring dependencies", "Using it without configuration"],
            "explanation": f"Understanding {t} requires grasping its architecture.",
            "bloom_level": "Understand",
            "difficulty": "Easy",
        },
        {
            "question": f"What benefit does scalability bring when using {t}?",
            "options": [f"Handling increased load without major redesign", "Fixing bugs automatically", "Eliminating monitoring needs", "Reducing initial setup time"],
            "explanation": f"{t} scalability enables growth.",
            "bloom_level": "Apply",
            "difficulty": "Hard",
        },
        {
            "question": f"What is typically required to effectively apply {t}?",
            "options": [f"Understanding core concepts and practical experience", "Only theoretical knowledge", "Memorizing commands", "Using a single configuration"],
            "explanation": f"Applying {t} effectively requires both knowledge and practice.",
            "bloom_level": "Apply",
            "difficulty": "Medium",
        },
        {
            "question": f"Why might organizations adopt {t}?",
            "options": [f"To standardize and streamline workflows", "To eliminate all manual processes", "To replace existing systems entirely", "To reduce team size"],
            "explanation": f"{t} helps organizations improve efficiency.",
            "bloom_level": "Understand",
            "difficulty": "Easy",
        },
        {
            "question": f"What makes {t} different from legacy approaches?",
            "options": [f"Modern design prioritizing flexibility and automation", "Requiring more manual intervention", "Being limited to older systems", "Lack of community support"],
            "explanation": f"{t} represents a modern approach to its domain.",
            "bloom_level": "Understand",
            "difficulty": "Hard",
        },
    ]
    result = []
    for i, tmpl in enumerate(templates[:num_questions]):
        mcq = {
            "question": tmpl["question"],
            "options": tmpl["options"],
            "correct_answer": tmpl["options"][0],
            "explanation": tmpl["explanation"],
            "bloom_level": tmpl["bloom_level"],
            "difficulty": tmpl["difficulty"],
        }
        result.append(mcq)
    return result


def _is_conceptual_sentence(sent: str) -> bool:
    """True if sentence has conceptual/logic indicators."""
    lower = sent.lower()
    return any(s in lower for s in CONCEPTUAL_STARTERS)


def _check_done(mcqs: List[Dict], total_target: int, target_by_difficulty: Optional[Dict[str, int]]) -> bool:
    """Return True if we should stop (enough MCQs)."""
    if len(mcqs) >= total_target:
        return True
    if target_by_difficulty:
        counts = {d: sum(1 for m in mcqs if m.get("difficulty") == d) for d in DIFFICULTY_LEVELS}
        return all(counts.get(d, 0) >= target_by_difficulty.get(d, 0) for d in DIFFICULTY_LEVELS)
    return False


def _generate_mcq_transformers(context: str, num_questions: int = 3) -> List[Dict]:
    """Generate MCQs using HuggingFace T5 or similar model."""
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    except ImportError:
        return []

    model_path = os.path.join(MODELS_FOLDER, "mcq_generator")
    if not os.path.isdir(model_path):
        try:
            pipe = pipeline("text2text-generation", model="google/flan-t5-base", max_length=256)
        except Exception:
            return []
    else:
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
            pipe = pipeline("text2text-generation", model=model, tokenizer=tokenizer, max_length=256)
        except Exception:
            return []

    results = []
    chunks = [context[i:i+500] for i in range(0, min(len(context), 2000), 500)][:num_questions]
    conceptual_prompt = (
        "Generate a conceptual or logic-based multiple choice question that tests understanding, "
        "not memorization. Focus on why, how, or relationships. Question from: "
    )
    for chunk in chunks:
        try:
            clean_chunk = re.sub(r'\s+', ' ', chunk[:300]).strip()
            out = pipe(conceptual_prompt + clean_chunk)[0]["generated_text"]
            # Parse simple Q? A) B) C) D) format
            q = out.split("?")[0].strip() + "?"
            options = re.findall(r'[A-D]\)\s*([^\n]+)', out)
            if len(options) >= 2:
                bloom = classify_bloom(q)
                mcq = {
                    "question": q,
                    "options": options[:4],
                    "correct_answer": options[0],
                    "explanation": chunk[:200],
                    "bloom_level": bloom,
                    "difficulty": _assign_difficulty_by_bloom(bloom),
                }
                if not _is_filename_based(mcq):
                    results.append(mcq)
        except Exception:
            continue
    return results


def _generate_conceptual_question(sent: str, context: str) -> Optional[Dict]:
    """Generate a why/how/explain MCQ from a conceptual sentence. Uses content-derived options when possible."""
    lower = sent.lower()
    from .nlp_processing import extract_keywords
    kw = extract_keywords(context, 15)
    # Plausible distractors from context (related terms that aren't the answer)
    distractors = [w for w in kw if len(w) > 3 and w.lower() not in sent.lower()][:5]
    generic_opts = {
        "cause": ["The cause-effect relationship described in the passage", "A tangential definition", "An unrelated example", "A restatement without explanation"],
        "imply": ["The logical consequence described in the text", "A superficial restatement", "An unrelated fact", "A definition that misses the point"],
        "explain": ["The explanation or reasoning given in the passage", "A summary that omits key reasoning", "A definition without context", "An unrelated comparison"],
        "compare": ["The distinction or comparison made in the text", "A superficial similarity only", "An unrelated difference", "A restatement that misses the contrast"],
    }
    if 'because' in lower or 'therefore' in lower:
        q = f"What best explains the following statement from the passage: \"{sent[:120]}...\""
        opts = generic_opts["cause"]
    elif 'means' in lower or 'implies' in lower:
        q = f"What does the passage imply by: \"{sent[:100]}...\""
        opts = generic_opts["imply"]
    elif 'how' in lower or 'why' in lower:
        q = f"According to the passage, which answer best addresses: \"{sent[:100]}...\""
        opts = generic_opts["explain"]
    elif any(s in lower for s in ('compare', 'contrast', 'difference')):
        q = f"Based on the passage: \"{sent[:110]}...\" What is the key distinction?"
        opts = generic_opts["compare"]
    elif any(s in lower for s in ('enables', 'allows', 'provides', 'supports')):
        q = f"What does the passage suggest about: \"{sent[:100]}...\""
        opts = ["The benefit or capability described in the text", "A minor detail only", "An assumption not in the passage", "A unrelated application"]
    else:
        return None
    return {
        "question": q,
        "options": opts[:4],
        "correct_answer": opts[0],
        "explanation": sent,
        "bloom_level": "Understand",
        "difficulty": "Medium",
    }


def _generate_content_comprehension(sent: str, context: str, keywords: List[str]) -> Optional[Dict]:
    """Generate content-based comprehension MCQ. Options derived from text."""
    if len(sent) < 25:
        return None
    from .nlp_processing import extract_keywords
    kw = keywords or extract_keywords(context, 20)
    # Main idea style - varies difficulty
    templates = [
        ("Based on the passage, what is the main point of: \"{s}\"", "Understand", "Medium"),
        ("According to the text, which best describes: \"{s}\"", "Remember", "Easy"),
        ("The passage indicates that \"{s}\" What follows from this?", "Apply", "Hard"),
        ("What does the content suggest about the relationship in: \"{s}\"", "Analyze", "Hard"),
    ]
    s = sent[:100] + "..." if len(sent) > 100 else sent
    q_t, bloom, diff = random.choice(templates)
    q = q_t.format(s=s)
    opts = [
        "The idea or relationship described in the passage",
        "A detail that is mentioned but not central",
        "An implication that goes beyond the text",
        "A tangential or unrelated point",
    ]
    return {
        "question": q,
        "options": opts[:4],
        "correct_answer": opts[0],
        "explanation": sent,
        "bloom_level": bloom,
        "difficulty": diff,
    }


def _generate_mcq_rulebased(
    context: str,
    num_questions: int = 5,
    target_by_difficulty: Optional[Dict[str, int]] = None,
    prefer_conceptual: bool = False,
) -> List[Dict]:
    """Rule-based MCQ: generates conceptual, comprehension, and fill-in-blank from content. Prefers conceptual."""
    from .nlp_processing import segment_sentences, extract_keywords

    sentences = segment_sentences(context)
    if not sentences:
        chunks = re.split(r'\n\s*\n|\s{2,}', context)
        sentences = [c.strip() for c in chunks if len(c.strip()) >= 15 and is_readable_text(c.strip())]
    if not sentences:
        sentences = [ln.strip() for ln in context.split('\n') if len(ln.strip()) >= 12 and is_readable_text(ln.strip())]

    if not sentences:
        return []

    keywords_all = extract_keywords(context, 30)

    def score(s):
        sc = 3.0 if _is_conceptual_sentence(s) else 0.8  # Strongly prefer conceptual
        if 40 <= len(s) <= 250:
            sc += 1.2
        elif 25 <= len(s) < 40:
            sc += 0.8
        elif len(s) > 250:
            sc += 0.6
        return sc

    sentences = sorted(sentences, key=score, reverse=True)

    mcqs = []
    seen = set()
    total_target = sum(target_by_difficulty.values()) if target_by_difficulty else num_questions
    max_iter = max(total_target * 3, 80)

    for sent in sentences[:min(len(sentences), max_iter)]:
        if len(sent) < 20 or sent in seen:
            continue
        if not is_readable_text(sent):
            continue
        seen.add(sent)

        if FILENAME_EXT_PATTERN.search(sent):
            continue

        # 1. Conceptual sentences -> conceptual question (highest priority)
        if _is_conceptual_sentence(sent):
            conceptual_mcq = _generate_conceptual_question(sent, context)
            if conceptual_mcq and not _is_filename_based(conceptual_mcq):
                mcqs.append(conceptual_mcq)
                if _check_done(mcqs, total_target, target_by_difficulty):
                    return mcqs
                continue

        # 2. Content-based comprehension (mid-length+ sentences) - more conceptual
        if len(sent) >= 35 and random.random() < 0.85:
            comp_mcq = _generate_content_comprehension(sent, context, keywords_all)
            if comp_mcq and not _is_filename_based(comp_mcq):
                mcqs.append(comp_mcq)
                if _check_done(mcqs, total_target, target_by_difficulty):
                    return mcqs
                continue

        # 3. Fill-in-blank (fallback for recall)
        keywords = [w for w in extract_keywords(sent, 15) if len(w) >= 3 and '.' not in w and not re.match(r'[\w\-]+\.\w+', w)][:8]
        if not keywords:
            keywords = re.findall(r'\b[a-zA-Z]{3,}\b', sent.lower())
            keywords = [w for w in keywords if w not in {'that', 'this', 'with', 'from', 'have', 'been', 'when', 'what', 'which', 'their', 'there'}][:8]
        if not keywords:
            # Fallback: comprehension-style question from the sentence
            q = f"According to the passage, which best captures the main idea of: \"{sent[:100]}...\"?"
            opts = ["The main idea or concept described in the passage", "A minor supporting detail only", "An unrelated or tangential point", "A partial summary missing key elements"]
            mcq = {
                "question": q,
                "options": opts,
                "correct_answer": opts[0],
                "explanation": sent,
                "bloom_level": "Understand",
                "difficulty": "Medium",
            }
            if not _is_filename_based(mcq):
                mcqs.append(mcq)
            if _check_done(mcqs, total_target, target_by_difficulty):
                return mcqs
            continue
        target = random.choice(keywords)
        if '.' in target:
            continue
        pattern = re.compile(re.escape(target), re.IGNORECASE)
        blanked = pattern.sub("______", sent, count=1)
        question = f"Fill in the blank: {blanked}"

        wrong = [w for w in extract_keywords(context, 40) if w.lower() != target.lower() and len(w) >= 3 and '.' not in w][:6]
        if not wrong:
            wrong = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', context.lower()) if w != target.lower()][:6]
        options = [target] + [w for w in wrong if w.lower() not in [target.lower()]][:3]
        random.shuffle(options)

        bloom = classify_bloom(question)
        difficulty = "Medium"
        if bloom == "Remember" and len(sent) < 120:
            difficulty = "Easy"
        elif bloom in ("Apply", "Analyze") or len(sent) > 150:
            difficulty = "Hard"

        mcq = {
            "question": question,
            "options": options,
            "correct_answer": target,
            "explanation": sent,
            "bloom_level": bloom,
            "difficulty": difficulty,
        }
        if not _is_filename_based(mcq):
            mcqs.append(mcq)

        if _check_done(mcqs, total_target, target_by_difficulty):
            return mcqs

    return mcqs


def _assign_difficulty_by_bloom(bloom_level: str) -> str:
    """Map Bloom level to difficulty."""
    if bloom_level == "Remember":
        return "Easy"
    if bloom_level == "Understand":
        return "Medium"
    if bloom_level == "Apply":
        return "Hard"
    if bloom_level == "Analyze":
        return "Hard"
    return "Medium"


def generate_mcqs(
    text: str,
    num_questions: int = 12,
    num_easy: Optional[int] = None,
    num_medium: Optional[int] = None,
    num_hard: Optional[int] = None,
    use_transformer: bool = True,
    from_audio_video: bool = False,
    topic_fallback: Optional[str] = None,
) -> List[Dict]:
    """
    Generate MCQs from lecture text with Easy, Medium, Hard levels.
    Returns list of {question, options, correct_answer, explanation, bloom_level, difficulty}.
    If num_easy/num_medium/num_hard are set, generates that many per level. Otherwise splits num_questions.
    """
    # Normalize to 4 options and ensure difficulty field
    def ensure_four_options(mcq: Dict) -> Dict:
        opts = mcq.get("options", [])
        correct = mcq.get("correct_answer", "")
        if correct not in opts:
            opts = [correct] + opts
        while len(opts) < 4 and len(opts) > 0:
            opts.append(f"Option {len(opts)+1}")
        mcq["options"] = opts[:4]
        if "difficulty" not in mcq:
            mcq["difficulty"] = _assign_difficulty_by_bloom(mcq.get("bloom_level", "Understand"))
        return mcq

    target = None
    if num_easy is not None or num_medium is not None or num_hard is not None:
        target = {
            "Easy": max(0, num_easy or 0),
            "Medium": max(0, num_medium or 0),
            "Hard": max(0, num_hard or 0),
        }
        total_target = sum(target.values())
        if total_target == 0:
            target = None

    num_q = num_questions if target is None else sum(target.values())

    mcqs = []
    # For topic fallback (video/audio with no transcript): use conceptual topic MCQs
    if topic_fallback and len(topic_fallback.strip()) > 1:
        mcqs = _generate_topic_conceptual_mcqs(topic_fallback.strip(), num_q)

    if not mcqs and use_transformer:
        mcqs = _generate_mcq_transformers(text, num_q)

    # Try to extract topic from seed content for topic-based fallback
    if not mcqs and from_audio_video and not topic_fallback:
        import re
        m = re.match(r"^(\w[\w\s]+?)\s+is\s+a\s+widely\s+used", text.strip(), re.IGNORECASE)
        if m:
            topic_fallback = m.group(1).strip()
            if len(topic_fallback) > 1 and len(topic_fallback) < 50:
                mcqs = _generate_topic_conceptual_mcqs(topic_fallback, num_q)

    if not mcqs:
        mcqs = _generate_mcq_rulebased(
            text,
            num_q,
            target_by_difficulty=target,
            prefer_conceptual=from_audio_video,
        )

    # If we got too few from rulebased, supplement with topic-based MCQs from keywords
    if len(mcqs) < num_q and text.strip():
        from .nlp_processing import extract_keywords
        keywords = extract_keywords(text, 5)
        if keywords and not topic_fallback:
            topic_fallback = " ".join(keywords[:2]).title()
        if topic_fallback and len(topic_fallback.strip()) > 1:
            extra = _generate_topic_conceptual_mcqs(topic_fallback.strip(), min(num_q - len(mcqs), 12))
            extra = [m for m in extra if not _is_filename_based(m)]
            mcqs = mcqs + extra[: num_q - len(mcqs)]

    by_diff: Dict[str, List[Dict]] = {"Easy": [], "Medium": [], "Hard": []}
    for m in mcqs:
        d = m.get("difficulty", "Medium")
        if d in by_diff:
            by_diff[d].append(m)

    result: List[Dict] = []
    if target:
        want_e = target["Easy"]
        want_m = target["Medium"]
        want_h = target["Hard"]
        result.extend(by_diff["Easy"][:want_e])
        result.extend(by_diff["Medium"][:want_m])
        result.extend(by_diff["Hard"][:want_h])
        leftover: List[Dict] = []
        leftover.extend(by_diff["Easy"][want_e:])
        leftover.extend(by_diff["Medium"][want_m:])
        leftover.extend(by_diff["Hard"][want_h:])
        for m in leftover:
            if len(result) < num_q:
                result.append(m)
    else:
        per_level = max(1, num_q // 3)
        for level in DIFFICULTY_LEVELS:
            result.extend(by_diff[level][:per_level])
        for level in DIFFICULTY_LEVELS:
            for m in by_diff[level][per_level:]:
                if len(result) < num_q:
                    result.append(m)
        easy_c = sum(1 for m in result if m.get("difficulty") == "Easy")
        med_c = sum(1 for m in result if m.get("difficulty") == "Medium")
        hard_c = sum(1 for m in result if m.get("difficulty") == "Hard")
        if easy_c == 0 or med_c == 0 or hard_c == 0:
            for i, m in enumerate(result):
                m["difficulty"] = DIFFICULTY_LEVELS[i % 3]

    mcqs = result[:num_q]

    # Final filter: remove filename-based, UUID, garbled, and low-quality
    mcqs = [
        m for m in mcqs
        if not _is_filename_based(m) and not _contains_uuid_or_bad(m) and not _contains_garbled_text(m)
    ]
    return [ensure_four_options(m) for m in mcqs]
