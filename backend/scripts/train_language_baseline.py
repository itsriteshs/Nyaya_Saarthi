"""Fit a character TF-IDF language classifier on the leakage-safe derived split."""
import csv
import json
import time
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.preprocessing import normalize_text
from scripts.prepare_nlp_data import MANIFEST, prepare

MODEL = BACKEND_DIR / "artifacts" / "language_model.joblib"
META = BACKEND_DIR / "artifacts" / "language_model_metadata.json"

def train():
    if not MANIFEST.exists(): prepare()
    with MANIFEST.open(encoding="utf-8", newline="") as f:
        split = {x["utterance_id"]:x["derived_split"] for x in csv.DictReader(f)}
    _, rows = load_dataset(DATASET_DIR / "annotated_utterances.csv")
    parts = {k:([],[]) for k in ("train","dev")}
    for _, row in rows:
        part = split.get(row.get("utterance_id"))
        if part in parts:
            parts[part][0].append(normalize_text(row["text"]))
            parts[part][1].append(row["language"].lower())
    model = Pipeline([("tfidf",TfidfVectorizer(analyzer="char_wb",ngram_range=(2,5),max_features=80000,min_df=2)),
                      ("classifier",LinearSVC(random_state=18))])
    start=time.perf_counter(); model.fit(*parts["train"])
    prediction=model.predict(parts["dev"][0]);scores=np.asarray(model.decision_function(parts["dev"][0]))
    gaps=np.sort(scores,axis=1)[:,-1]-np.sort(scores,axis=1)[:,-2]
    correct=prediction==np.asarray(parts["dev"][1])
    threshold=float(np.quantile(gaps[correct],.10)) if correct.any() else float(np.quantile(gaps,.10))
    MODEL.parent.mkdir(parents=True,exist_ok=True);joblib.dump(model,MODEL,compress=3)
    meta={"model_version":"tfidf-language-v1","train_count":len(parts["train"][0]),"dev_count":len(parts["dev"][0]),
          "dev_accuracy":float(accuracy_score(parts["dev"][1],prediction)),
          "dev_report":classification_report(parts["dev"][1],prediction,output_dict=True,zero_division=0),
          "uncertainty_gap_threshold":threshold,"score_type":"SVM decision margin gap, not probability",
          "train_seconds":round(time.perf_counter()-start,3),"review_status":"pending human review"}
    META.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    return meta
if __name__=="__main__":print(json.dumps(train(),indent=2))
