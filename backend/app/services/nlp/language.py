"""Supervised language baseline plus script-aware uncertainty handling."""
import re
from functools import lru_cache
from pathlib import Path
import joblib
import numpy as np
from app.config import BACKEND_DIR

MODEL = BACKEND_DIR / "artifacts" / "language_model.joblib"
META = BACKEND_DIR / "artifacts" / "language_model_metadata.json"

@lru_cache(maxsize=1)
def load_language_model():
    if not MODEL.is_file() or not META.is_file():
        raise FileNotFoundError("Train the language baseline before inference")
    import json
    return joblib.load(MODEL), json.loads(META.read_text(encoding="utf-8"))

def analyze_language(text: str, requested: str):
    model, metadata = load_language_model()
    devanagari = bool(re.search(r"[\u0900-\u097f]", text))
    latin = bool(re.search(r"[A-Za-z]", text))
    if len(text.strip()) < 5:
        return {"requestedLanguage": requested, "detectedLanguage": "uncertain", "confidenceCategory": "low", "evidence": "Text is too short for reliable language classification"}
    if devanagari and latin:
        devanagari_letters = sum('\u0900' <= char <= '\u097f' for char in text)
        latin_letters = sum(char.isascii() and char.isalpha() for char in text)
        dominant_hindi = devanagari_letters > latin_letters
        return {"requestedLanguage": requested, "detectedLanguage": "hindi" if dominant_hindi else "mixed",
                "confidenceCategory": "high" if dominant_hindi else "low",
                "evidence": "Devanagari is dominant" if dominant_hindi else "Mixed scripts without Devanagari dominance"}
    if devanagari and not latin:
        return {"requestedLanguage": requested, "detectedLanguage": "hindi", "confidenceCategory": "high", "evidence": "Devanagari script occurs"}
    label = str(model.predict([text])[0]).lower()
    scores = np.asarray(model.decision_function([text]))
    gap = float(np.sort(scores[0])[-1] - np.sort(scores[0])[-2]) if scores.ndim == 2 else abs(float(scores[0]))
    low = gap < metadata["uncertainty_gap_threshold"]
    return {"requestedLanguage": requested, "detectedLanguage": "uncertain" if low else label,
            "confidenceCategory": "low" if low else "medium", "evidence": f"Character TF-IDF language classifier; decision gap {gap:.3f} (not probability)",
            "candidateLanguage": label if low else None}
