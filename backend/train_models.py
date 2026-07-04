#!/usr/bin/env python3
"""
Lecturify AI - Training Pipeline
Auto-loads datasets from datasets/, trains MCQ generator & Bloom classifier.
Run from project root: python backend/train_models.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

try:
    from backend.config import DATASET_PATH, MODELS_FOLDER
    from backend.services.dataset_loader import load_mcq_training_data, load_bloom_training_data, datasets_available
except ImportError:
    from config import DATASET_PATH, MODELS_FOLDER
    from services.dataset_loader import load_mcq_training_data, load_bloom_training_data, datasets_available


def train_bloom_classifier():
    """Train Bloom taxonomy classifier (rule-based + optional sklearn)."""
    bloom_data = load_bloom_training_data()
    if not bloom_data:
        print("[Bloom] No Bloom training data found. Using rule-based only.")
        return False

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.ensemble import RandomForestClassifier
        import joblib
    except ImportError:
        print("[Bloom] sklearn not installed. Using rule-based classifier only.")
        return False

    X = [d["question"] for d in bloom_data]
    y = [d["bloom_level"] for d in bloom_data]

    valid_levels = {"Remember", "Understand", "Apply"}
    filtered = [(x, yi) for x, yi in zip(X, y) if yi in valid_levels]
    if not filtered:
        print("[Bloom] No valid labels. Skipping.")
        return False

    X, y = zip(*filtered)
    vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    X_vec = vec.fit_transform(X)

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X_vec, y)

    os.makedirs(MODELS_FOLDER, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_FOLDER, "bloom_classifier.pkl"))
    joblib.dump(vec, os.path.join(MODELS_FOLDER, "bloom_vectorizer.pkl"))
    print(f"[Bloom] Trained on {len(X)} samples. Saved to {MODELS_FOLDER}")
    return True


def train_mcq_generator():
    """Train MCQ generator using T5/Seq2Seq if datasets available."""
    mcq_data = load_mcq_training_data()
    if not mcq_data or len(mcq_data) < 50:
        print("[MCQ] Insufficient MCQ training data for fine-tuning. Using inference-only.")
        return False

    try:
        from transformers import T5ForConditionalGeneration, T5Tokenizer
        from torch.utils.data import Dataset
        import torch
    except ImportError:
        print("[MCQ] transformers/torch not installed. Skipping MCQ model training.")
        return False

    os.makedirs(MODELS_FOLDER, exist_ok=True)
    model_name = "google/flan-t5-base"
    try:
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
    except Exception as e:
        print(f"[MCQ] Could not load {model_name}: {e}")
        return False

    # Save base model for inference (no fine-tuning without more setup)
    save_path = os.path.join(MODELS_FOLDER, "mcq_generator")
    tokenizer.save_pretrained(save_path)
    model.save_pretrained(save_path)
    print(f"[MCQ] Saved base T5 model to {save_path}. Use with generate_mcqs().")
    return True


def main():
    print("Lecturify AI - Training Pipeline")
    print(f"Dataset path: {DATASET_PATH}")
    print(f"Models path: {MODELS_FOLDER}")

    if not datasets_available():
        print("No datasets found. Running in inference-only mode.")
        print("Place CSV/JSON datasets in datasets/ folder and run again.")
        return

    train_bloom_classifier()
    train_mcq_generator()
    print("Training complete.")


if __name__ == "__main__":
    main()
