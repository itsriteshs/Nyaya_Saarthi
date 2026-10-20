"""Offline grouped-split NLP evaluation; keeps production artifacts untouched."""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.entity_extractor import build_status_vocabulary, extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.preprocessing import normalize_text
from app.services.nlp.slot_detector import detect_slots

ROOT = BACKEND_DIR / "experiments"
SUPPORTED = {"VEHICLE_CLASS", "OBSERVED_SPEED", "ROAD_TYPE", "STATE", "EVENT_DATE", "INSURANCE_STATUS", "CHALLAN_STATUS", "LICENCE_STATUS", "AGE"}


def prf(tp, fp, fn):
    return {"precision": tp / (tp + fp) if tp + fp else 0,
            "recall": tp / (tp + fn) if tp + fn else 0,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0,
            "tp": tp, "fp": fp, "fn": fn}


def language_prediction(text, model, threshold):
    devanagari = bool(re.search(r"[\u0900-\u097f]", text))
    latin = bool(re.search(r"[A-Za-z]", text))
    if len(text.strip()) < 5: return "uncertain"
    if devanagari and latin:
        devanagari_letters = sum("\u0900" <= c <= "\u097f" for c in text)
        latin_letters = sum(c.isascii() and c.isalpha() for c in text)
        return "hindi" if devanagari_letters > latin_letters else "mixed"
    if devanagari: return "hindi"
    score = np.asarray(model.decision_function([normalize_text(text)]))[0]
    gap = float(np.sort(score)[-1] - np.sort(score)[-2])
    return "uncertain" if gap < threshold else str(model.classes_[np.argmax(score)])


def legacy_language_prediction(text, model, threshold):
    """Pre Phase 6 script policy on the same grouped split for paired comparison."""
    devanagari = bool(re.search(r"[\u0900-\u097f]", text))
    latin = bool(re.search(r"[A-Za-z]", text))
    if len(text.strip()) < 5: return "uncertain"
    if devanagari and latin: return "mixed"
    if devanagari: return "hindi"
    score = np.asarray(model.decision_function([normalize_text(text)]))[0]
    gap = float(np.sort(score)[-1] - np.sort(score)[-2])
    return "uncertain" if gap < threshold else str(model.classes_[np.argmax(score)])


def run():
    path = ROOT / "manifests" / "phase6_grouped_split.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        splits = {r["utterance_id"]: r["split"] for r in csv.DictReader(stream)}
    _, raw = load_dataset(DATASET_DIR / "annotated_utterances.csv")
    rows = {part: [] for part in ("train", "dev", "test")}
    for _, row in raw:
        if isinstance(row, dict) and splits.get(row.get("utterance_id")) in rows:
            rows[splits[row["utterance_id"]]].append(row)
    train, dev, test = rows["train"], rows["dev"], rows["test"]
    x_train = [normalize_text(r["text"]) for r in train]
    y_train = [r["primary_intent_id"] for r in train]
    x_dev = [normalize_text(r["text"]) for r in dev]
    y_dev = [r["primary_intent_id"] for r in dev]
    candidates = {
        "char_svm": Pipeline([("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=100000)),
                              ("classifier", LinearSVC(random_state=471))]),
        "word_lr": Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=70000,
                                                          token_pattern=r"(?u)\b\w+\b")),
                            ("classifier", LogisticRegression(max_iter=400, random_state=471))])}
    dev_results = {}
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        predicted = model.predict(x_dev)
        dev_results[name] = {"accuracy": float(accuracy_score(y_dev, predicted)),
                             "macroF1": float(f1_score(y_dev, predicted, average="macro", zero_division=0))}
    selected = max(dev_results, key=lambda k: (dev_results[k]["macroF1"], dev_results[k]["accuracy"], k == "char_svm"))
    intent_model = candidates[selected]
    language_model = Pipeline([("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), max_features=80000, min_df=2)),
                               ("classifier", LinearSVC(random_state=471))])
    language_model.fit(x_train, [r["language"].lower() for r in train])
    dev_scores = np.asarray(language_model.decision_function(x_dev))
    dev_gaps = np.sort(dev_scores, axis=1)[:, -1] - np.sort(dev_scores, axis=1)[:, -2]
    dev_correct = language_model.predict(x_dev) == np.asarray([r["language"].lower() for r in dev])
    threshold = float(np.quantile(dev_gaps[dev_correct], .10)) if dev_correct.any() else float(np.quantile(dev_gaps, .10))
    vocab = build_status_vocabulary({r["utterance_id"] for r in train})
    x_test = [normalize_text(r["text"]) for r in test]
    true_intents = [r["primary_intent_id"] for r in test]
    pred_intents = list(intent_model.predict(x_test))
    true_languages = [r["language"].lower() for r in test]
    pred_languages = [language_prediction(r["text"], language_model, threshold) for r in test]
    legacy_languages = [legacy_language_prediction(r["text"], language_model, threshold) for r in test]
    entity_tp = entity_fp = entity_fn = 0
    slot = Counter()
    oracle_slot = Counter()
    by_type = defaultdict(Counter)
    predictions = []
    for row, predicted_intent, predicted_language in zip(test, pred_intents, pred_languages):
        entities = [normalize(e) for e in extract(row["text"], status_values=vocab)]
        gold = {(e["slot_name"], e["start"], e["end"]) for e in json.loads(row["entity_annotations_json"] or "[]")
                if e.get("slot_name") in SUPPORTED and isinstance(e.get("start"), int) and isinstance(e.get("end"), int)}
        found = {(e["type"], e["start"], e["end"]) for e in entities if e["type"] in SUPPORTED}
        entity_tp += len(gold & found); entity_fp += len(found - gold); entity_fn += len(gold - found)
        for item in gold & found: by_type[item[0]]["tp"] += 1
        for item in found - gold: by_type[item[0]]["fp"] += 1
        for item in gold - found: by_type[item[0]]["fn"] += 1
        gold_slots = set(filter(None, row["missing_slots"].split("|")))
        predicted_slots = {s["slot"] for s in detect_slots(predicted_intent, entities)["missingSlots"]}
        oracle_slots = {s["slot"] for s in detect_slots(row["primary_intent_id"], entities)["missingSlots"]}
        for target, found_slots in ((slot, predicted_slots), (oracle_slot, oracle_slots)):
            target["tp"] += len(found_slots & gold_slots)
            target["fp"] += len(found_slots - gold_slots)
            target["fn"] += len(gold_slots - found_slots)
            target["exact"] += found_slots == gold_slots
        predictions.append({"caseId": row["utterance_id"], "trueIntent": row["primary_intent_id"],
                            "predictedIntent": predicted_intent, "trueLanguage": row["language"].lower(),
                            "predictedLanguage": predicted_language, "goldEntities": len(gold),
                            "predictedEntities": len(found), "matchedEntities": len(gold & found),
                            "goldMissingSlots": sorted(gold_slots), "predictedMissingSlots": sorted(predicted_slots),
                            "oracleIntentMissingSlots": sorted(oracle_slots)})
    labels = sorted(set(true_intents) | set(pred_intents))
    language_labels = sorted(set(true_languages) | set(pred_languages))
    answered = [i for i, label in enumerate(pred_languages) if label != "uncertain"]
    legacy_answered = [i for i, label in enumerate(legacy_languages) if label != "uncertain"]
    result = {"label": "exploratory grouped split; annotations pending review; original test already exposed",
              "manifest": path.name, "counts": {k: len(v) for k, v in rows.items()},
              "intent": {"selected": selected, "devCandidates": dev_results,
                         "accuracy": float(accuracy_score(true_intents, pred_intents)),
                         "macroF1": float(f1_score(true_intents, pred_intents, average="macro", zero_division=0)),
                         "weightedF1": float(f1_score(true_intents, pred_intents, average="weighted", zero_division=0)),
                         "perIntent": classification_report(true_intents, pred_intents, output_dict=True, zero_division=0),
                         "labels": labels, "confusion": confusion_matrix(true_intents, pred_intents, labels=labels).tolist()},
              "language": {"thresholdFromDev": threshold, "coverage": len(answered) / len(test),
                           "legacyPolicyOnSameSplit": {"coverage": len(legacy_answered) / len(test),
                                                       "accuracyAnswered": sum(legacy_languages[i] == true_languages[i] for i in legacy_answered) / len(legacy_answered) if legacy_answered else None,
                                                       "overallAccuracy": float(accuracy_score(true_languages, legacy_languages))},
                           "accuracyAnswered": sum(pred_languages[i] == true_languages[i] for i in answered) / len(answered) if answered else None,
                           "overallAccuracy": float(accuracy_score(true_languages, pred_languages)),
                           "perLanguage": classification_report(true_languages, pred_languages, output_dict=True, zero_division=0),
                           "labels": language_labels, "confusion": confusion_matrix(true_languages, pred_languages, labels=language_labels).tolist()},
              "entityExactSpan": {**prf(entity_tp, entity_fp, entity_fn),
                                  "byType": {k: prf(v["tp"], v["fp"], v["fn"]) for k, v in by_type.items()}},
              "missingSlots": {**prf(slot["tp"], slot["fp"], slot["fn"]), "exactSetAccuracy": slot["exact"] / len(test),
                               "oracleIntent": {**prf(oracle_slot["tp"], oracle_slot["fp"], oracle_slot["fn"]),
                                                "exactSetAccuracy": oracle_slot["exact"] / len(test)}},
              "limitations": ["Status phrase vocabulary learned from grouped train rows only.",
                              "Rule-based entity extractor was developed using previously exposed examples; this is not independent validation.",
                              "Missing-slot reference labels mix required and conditional slots; oracle-intent analysis isolates only one error source."]}
    metrics_path = ROOT / "metrics" / "phase6_nlp.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    pred_path = ROOT / "predictions" / "phase6_nlp.jsonl"
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    pred_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in predictions), encoding="utf-8")
    return {"counts": result["counts"], "intent": {k: result["intent"][k] for k in ("selected", "accuracy", "macroF1", "weightedF1")},
            "language": {k: result["language"][k] for k in ("coverage", "accuracyAnswered", "overallAccuracy")},
            "entityF1": result["entityExactSpan"]["f1"], "slotF1": result["missingSlots"]["f1"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
