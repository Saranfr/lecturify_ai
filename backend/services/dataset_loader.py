"""
Lecturify AI - Dataset Loader
Auto-scans datasets/ directory, loads CSV/JSON/TXT for training.
"""
import os
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple

try:
    from backend.config import DATASET_PATH
except ImportError:
    from config import DATASET_PATH


def _scan_directory(base_path: str) -> Tuple[List[str], List[str], List[str]]:
    """Scan directory for CSV, JSON, TXT files recursively."""
    csv_files, json_files, txt_files = [], [], []
    if not os.path.exists(base_path):
        return csv_files, json_files, txt_files

    for root, _, files in os.walk(base_path):
        for f in files:
            fp = os.path.join(root, f)
            lower = f.lower()
            if lower.endswith(".csv"):
                csv_files.append(fp)
            elif lower.endswith(".json"):
                json_files.append(fp)
            elif lower.endswith(".txt"):
                txt_files.append(fp)
    return csv_files, json_files, txt_files


def load_mcq_training_data() -> List[Dict]:
    """
    Load MCQ training data from datasets.
    Supports: SciQ CSV (question, correct_answer, distractor1-3, support),
              SQuAD JSON, RACE CSV.
    """
    results = []
    base = DATASET_PATH if os.path.isabs(DATASET_PATH) else DATASET_PATH
    csv_files, json_files, _ = _scan_directory(base)

    # SciQ format: question, correct_answer, distractor1, distractor2, distractor3, support
    for fp in csv_files:
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    q = row.get("question", "").strip()
                    if not q:
                        continue
                    correct = row.get("correct_answer", row.get("answer", ""))
                    distractors = [
                        row.get("distractor1", row.get("distractor", "")),
                        row.get("distractor2", ""),
                        row.get("distractor3", ""),
                    ]
                    if isinstance(row.get("distractor"), str) and "[" in str(row.get("distractor", "")):
                        import ast
                        try:
                            distractors = ast.literal_eval(str(row.get("distractor", "[]")))
                        except Exception:
                            pass
                    support = row.get("support", "")
                    results.append({
                        "question": q,
                        "correct_answer": correct,
                        "distractors": [d for d in distractors if d],
                        "explanation": support,
                    })
        except Exception as e:
            print(f"[dataset_loader] Skip {fp}: {e}")

    # SQuAD format
    for fp in json_files:
        if "squad" in fp.lower() or "train-v1" in fp or "dev-v1" in fp:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for article in data.get("data", []):
                    for para in article.get("paragraphs", []):
                        context = para.get("context", "")
                        for qa in para.get("qas", []):
                            q = qa.get("question", "")
                            ans = qa.get("answers", [{}])[0].get("text", "") if qa.get("answers") else ""
                            results.append({
                                "question": q,
                                "context": context,
                                "correct_answer": ans,
                                "distractors": [],
                                "explanation": context[:500],
                            })
            except Exception as e:
                print(f"[dataset_loader] Skip {fp}: {e}")

    return results


def load_bloom_training_data() -> List[Dict]:
    """
    Load Bloom taxonomy training data (question -> bloom_level).
    Supports: combined_bloom.json, combined_bloom_small.json (question, bloom_level).
    """
    results = []
    base = DATASET_PATH if os.path.isabs(DATASET_PATH) else DATASET_PATH
    _, json_files, _ = _scan_directory(base)

    bloom_map = {"remember": "Remember", "understand": "Understand", "apply": "Apply",
                 "analyze": "Understand", "evaluate": "Apply", "create": "Apply"}

    for fp in json_files:
        if "bloom" not in fp.lower():
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data if isinstance(data, list) else [data]:
                q = item.get("question", "").strip()
                level = item.get("bloom_level", item.get("bloom", "Understand"))
                if isinstance(level, str):
                    level = bloom_map.get(level.lower(), level)
                if q and level in ("Remember", "Understand", "Apply"):
                    results.append({"question": q, "bloom_level": level})
        except Exception as e:
            print(f"[dataset_loader] Skip {fp}: {e}")

    return results


def datasets_available() -> bool:
    """Check if any training datasets exist."""
    base = DATASET_PATH
    if not os.path.exists(base):
        return False
    csv_f, json_f, _ = _scan_directory(base)
    return bool(csv_f or json_f)


def get_dataset_info() -> Dict:
    """Return info about available datasets."""
    base = DATASET_PATH
    csv_f, json_f, txt_f = _scan_directory(base)
    mcq = load_mcq_training_data()
    bloom = load_bloom_training_data()
    return {
        "dataset_path": base,
        "csv_files": len(csv_f),
        "json_files": len(json_f),
        "txt_files": len(txt_f),
        "mcq_samples": len(mcq),
        "bloom_samples": len(bloom),
        "training_available": len(mcq) > 0 or len(bloom) > 0,
    }
