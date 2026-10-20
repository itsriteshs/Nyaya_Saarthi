"""Audit annotations and prepare an offline grouped exploratory split.

Never rewrites source datasets or production model artifacts.
"""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.preprocessing import normalize_text, text_template

OUT = BACKEND_DIR / "experiments"


def run():
    _, raw = load_dataset(DATASET_DIR / "annotated_utterances.csv")
    rows = [r for _, r in raw if isinstance(r, dict) and r.get("utterance_id") and r.get("text")]
    _, gold_raw = load_dataset(DATASET_DIR / "gold_evaluation_cases.csv")
    gold_templates = {text_template(r.get("natural_query", "")) for _, r in gold_raw if isinstance(r, dict)}
    parent = list(range(len(rows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(a, b):
        a, b = root(a), root(b)
        if a != b: parent[b] = a

    by_scenario = {}
    by_template = {}
    for i, row in enumerate(rows):
        for table, key in ((by_scenario, row.get("scenario_id")), (by_template, text_template(row["text"]))):
            if key in table: join(i, table[key])
            else: table[key] = i

    groups = [root(i) for i in range(len(rows))]
    protected = {groups[i] for i, row in enumerate(rows) if text_template(row["text"]) in gold_templates}
    usable = [i for i, group in enumerate(groups) if group not in protected]
    x = np.asarray([rows[i]["text"] for i in usable])
    y = np.asarray([rows[i]["primary_intent_id"] for i in usable])
    g = np.asarray([groups[i] for i in usable])
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=471)
    train_dev, test = next(outer.split(x, y, g))
    inner = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=472)
    inner_train, inner_dev = next(inner.split(x[train_dev], y[train_dev], g[train_dev]))
    split = {usable[i]: "test" for i in test}
    split.update({usable[train_dev[i]]: "train" for i in inner_train})
    split.update({usable[train_dev[i]]: "dev" for i in inner_dev})
    assignments = []
    for i, row in enumerate(rows):
        assignments.append({"utterance_id": row["utterance_id"], "scenario_id": row.get("scenario_id", ""),
                            "group_id": hashlib.sha256(str(groups[i]).encode()).hexdigest()[:12],
                            "split": split.get(i, "excluded_gold_overlap"),
                            "intent_id": row["primary_intent_id"], "language": row["language"],
                            "source_split": row["split"]})
    assignments.sort(key=lambda r: r["utterance_id"])
    manifest = OUT / "manifests" / "phase6_grouped_split.csv"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(assignments[0]))
        writer.writeheader(); writer.writerows(assignments)
    observed = defaultdict(set)
    for item in assignments:
        if item["split"] in {"train", "dev", "test"}: observed[item["group_id"]].add(item["split"])
    assert all(len(parts) == 1 for parts in observed.values())
    originals = defaultdict(set)
    templates = defaultdict(set)
    exact = defaultdict(set)
    invalid_spans = 0
    unknown_entity_labels = Counter()
    script_label_mismatch = 0
    for row in rows:
        originals[row.get("scenario_id")].add(row["split"])
        templates[text_template(row["text"])].add(row["split"])
        exact[normalize_text(row["text"])].add(row["split"])
        text = row["text"]
        has_devanagari = any("\u0900" <= c <= "\u097f" for c in text)
        if row["language"].lower() == "english" and has_devanagari: script_label_mismatch += 1
        try: entities = json.loads(row.get("entity_annotations_json") or "[]")
        except ValueError:
            invalid_spans += 1
            continue
        for entity in entities:
            start, end = entity.get("start"), entity.get("end")
            if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end > len(text) or text[start:end] != entity.get("value"):
                invalid_spans += 1
            if entity.get("slot_name") == "AGE": unknown_entity_labels["AGE_PROVISIONAL"] += 1
    report = {"sourceRows": len(rows), "sourceSplits": dict(Counter(r["split"] for r in rows)),
              "groupedSplits": dict(Counter(r["split"] for r in assignments)),
              "groupCount": len(set(groups)), "scenarioCrossSourceSplits": sum(len(v) > 1 for v in originals.values()),
              "exactTextCrossSourceSplits": sum(len(v) > 1 for v in exact.values()),
              "digitMaskedTemplateCrossSourceSplits": sum(len(v) > 1 for v in templates.values()),
              "groupCrossDerivedSplits": sum(len(v) > 1 for v in observed.values()),
              "goldTemplateOverlapExcludedRows": sum(r["split"] == "excluded_gold_overlap" for r in assignments),
              "invalidAnnotationSpans": invalid_spans, "englishLabelWithDevanagari": script_label_mismatch,
              "provisionalEntityLabels": dict(unknown_entity_labels),
              "manifestSha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
              "limitations": ["All utterance labels remain pending human review.",
                              "The prior source test set was already exposed during Phase 2 development.",
                              "Scenario and digit-masked text grouping does not prove absence of semantic paraphrase leakage."]}
    path = OUT / "metrics" / "phase6_data_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
