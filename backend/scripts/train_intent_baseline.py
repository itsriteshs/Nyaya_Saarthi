"""Train and select a local, unreviewed-annotation intent baseline on derived splits."""
import csv
import json
import time
from collections import Counter
from pathlib import Path
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.preprocessing import normalize_text
from scripts.prepare_nlp_data import MANIFEST, prepare

ARTIFACT = BACKEND_DIR / "artifacts" / "intent_model.joblib"
METADATA = BACKEND_DIR / "artifacts" / "intent_model_metadata.json"

def data():
    if not MANIFEST.exists():
        prepare()
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        assignment = {row["utterance_id"]: row["derived_split"] for row in csv.DictReader(stream)}
    _, raw = load_dataset(DATASET_DIR / "annotated_utterances.csv")
    sets = {name: ([], []) for name in ("train", "dev", "test")}
    for _, row in raw:
        if not isinstance(row, dict) or row.get("utterance_id") not in assignment:
            continue
        split = assignment[row["utterance_id"]]
        if split in sets:
            sets[split][0].append(normalize_text(row["text"]))
            sets[split][1].append(row["primary_intent_id"])
    return sets

def margins(model, texts):
    scores = model.decision_function(texts)
    scores = np.asarray(scores)
    if scores.ndim == 1:
        return abs(scores)
    return np.sort(scores, axis=1)[:, -1] - np.sort(scores, axis=1)[:, -2]

def threshold_from_dev(gaps, correct):
    # Fit an error-flagging cutoff on dev only, maximizing balanced accuracy.
    if all(correct) or not any(correct):
        return float(np.quantile(gaps, .10))
    best = (-1.0, float(np.min(gaps)))
    for cutoff in np.unique(np.quantile(gaps, np.linspace(0, 1, 101))):
        flagged = gaps < cutoff
        tpr = float(np.mean(flagged[~correct]))
        tnr = float(np.mean(~flagged[correct]))
        quality = (tpr + tnr) / 2
        if quality > best[0]:
            best = (quality, float(cutoff))
    return best[1]

def train():
    sets = data()
    x_train, y_train = sets["train"]
    x_dev, y_dev = sets["dev"]
    if not x_train or not x_dev:
        raise ValueError("Derived training/development split is empty")
    candidates = {
        "word_lr": Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2, max_features=70000,
                                                        token_pattern=r"(?u)\b\w+\b")),
                             ("classifier", LogisticRegression(max_iter=400, random_state=18))]),
        "char_svm": Pipeline([("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3,5),
                                                         min_df=2, max_features=100000)),
                              ("classifier", LinearSVC(random_state=18))]),
    }
    results = {}
    fitted = {}
    for name, model in candidates.items():
        start = time.perf_counter()
        model.fit(x_train, y_train)
        predictions = model.predict(x_dev)
        results[name] = {"dev_accuracy": float(accuracy_score(y_dev, predictions)),
                         "dev_macro_f1": float(f1_score(y_dev, predictions, average="macro", zero_division=0)),
                         "dev_weighted_f1": float(f1_score(y_dev, predictions, average="weighted", zero_division=0)),
                         "train_seconds": round(time.perf_counter() - start, 3)}
        fitted[name] = model
    # A tied dev score favors character features for unseen spelling and transliteration.
    selected = max(results, key=lambda name: (results[name]["dev_macro_f1"], results[name]["dev_accuracy"], name == "char_svm"))
    model = fitted[selected]
    predicted = np.asarray(model.predict(x_dev))
    correct = predicted == np.asarray(y_dev)
    cutoff = threshold_from_dev(margins(model, x_dev), correct)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT, compress=3)
    manifest = json.loads((BACKEND_DIR / "reports" / "nlp_dataset_readiness.json").read_text())
    metadata = {"model_version": "tfidf-intent-v1", "selected_model": selected,
                "classes": list(model.classes_), "class_count": len(model.classes_),
                "train_count": len(x_train), "dev_count": len(x_dev), "test_count_untouched": len(sets["test"][0]),
                "train_language_review": "pending human review", "random_seed": 18,
                "manifest_sha256": manifest["manifest_sha256"], "candidate_dev_results": results,
                "score_type": "decision margin gap, not a probability" if selected == "char_svm" else "logit gap, not a probability",
                "uncertainty_gap_threshold": cutoff,
                "artifact": ARTIFACT.name, "sklearn_version": __import__("sklearn").__version__}
    METADATA.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata

if __name__ == "__main__":
    print(json.dumps(train(), indent=2))
