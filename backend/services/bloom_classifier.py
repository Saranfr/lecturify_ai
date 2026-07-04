"""
Lecturify AI - Bloom's Taxonomy Classifier
Classifies questions/concepts into Remember, Understand, Apply, Analyze.
"""
import os
from typing import Optional

try:
    from backend.config import BLOOM_LEVELS, MODELS_FOLDER
except ImportError:
    from config import BLOOM_LEVELS, MODELS_FOLDER

# Rule-based keyword patterns for Bloom levels
REMEMBER_KEYWORDS = [
    "what is", "who is", "when did", "where is", "list", "define", "name", "identify",
    "recall", "memorize", "state", "describe", "label", "match", "recognize",
]
UNDERSTAND_KEYWORDS = [
    "explain", "summarize", "interpret", "describe", "compare", "contrast",
    "classify", "discuss", "why", "how does", "translate", "paraphrase",
]
APPLY_KEYWORDS = [
    "apply", "use", "demonstrate", "solve", "implement", "calculate",
    "execute", "construct", "illustrate", "predict", "choose", "determine",
]
ANALYZE_KEYWORDS = [
    "analyze", "differentiate", "examine", "compare", "contrast",
    "distinguish", "infer", "break down", "relate", "attribute",
    "deconstruct", "investigate", "organize", "categorize",
]


def _rule_based_classify(question: str) -> str:
    """Rule-based classification using keyword patterns."""
    q = question.lower().strip()
    for kw in REMEMBER_KEYWORDS:
        if kw in q:
            return "Remember"
    for kw in UNDERSTAND_KEYWORDS:
        if kw in q:
            return "Understand"
    for kw in ANALYZE_KEYWORDS:
        if kw in q:
            return "Analyze" if "Analyze" in BLOOM_LEVELS else "Apply"
    for kw in APPLY_KEYWORDS:
        if kw in q:
            return "Apply"
    return "Understand"


def classify_bloom_ml(question: str, model_path: Optional[str] = None) -> str:
    """Classify using trained model if available."""
    path = model_path or os.path.join(MODELS_FOLDER, "bloom_classifier.pkl")
    if not os.path.isfile(path):
        return _rule_based_classify(question)

    try:
        import joblib
        model = joblib.load(path)
        vec_path = os.path.join(MODELS_FOLDER, "bloom_vectorizer.pkl")
        if os.path.isfile(vec_path):
            vec = joblib.load(vec_path)
            X = vec.transform([question])
            pred = model.predict(X)[0]
            return pred if pred in BLOOM_LEVELS else _rule_based_classify(question)
    except Exception:
        pass
    return _rule_based_classify(question)


def classify_bloom(question: str, use_ml: bool = True) -> str:
    """Classify question into Bloom level."""
    if use_ml:
        return classify_bloom_ml(question)
    return _rule_based_classify(question)
