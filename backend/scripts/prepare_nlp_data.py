"""Create a derived split manifest; never changes source annotations or split labels."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from app.config import DATASET_DIR, BACKEND_DIR, REPORT_DIR
from app.services.dataset_loader import load_dataset
from app.services.nlp.preprocessing import normalize_text, text_template

MANIFEST = BACKEND_DIR / "artifacts" / "nlp_split_manifest.csv"
SUMMARY = REPORT_DIR / "nlp_dataset_readiness.json"

def prepare():
    _, raw = load_dataset(DATASET_DIR / "annotated_utterances.csv")
    _, intents = load_dataset(DATASET_DIR / "intents.csv")
    _, gold = load_dataset(DATASET_DIR / "gold_evaluation_cases.csv")
    labels = {row["intent_id"] for _, row in intents if "intent_id" in row}
    gold_templates = {text_template(row["natural_query"]) for _, row in gold if row.get("natural_query")}
    valid = []
    invalid = []
    for line, row in raw:
        try:
            assert isinstance(row, dict) and row.get("utterance_id") and row.get("text", "").strip()
            assert row.get("primary_intent_id") in labels
            assert row.get("split") in {"train", "dev", "test"}
            entities = json.loads(row.get("entity_annotations_json") or "[]")
            assert isinstance(entities, list)
            assert all(isinstance(e, dict) for e in entities)
        except (AssertionError, ValueError, TypeError):
            invalid.append({"line": line, "id": row.get("utterance_id") if isinstance(row, dict) else None, "reason": "invalid text, label, split, or entity JSON"})
            continue
        valid.append((line, row))
    # Existing scenario groups are checked, not rewritten. Number-masked text
    # catches exact duplicates and a conservative class of template variants.
    by_scenario = defaultdict(set)
    by_template = defaultdict(set)
    for _, row in valid:
        by_scenario[row["scenario_id"]].add(row["split"])
        by_template[text_template(row["text"])].add(row["split"])
    scenario_cross = sum(len(x) > 1 for x in by_scenario.values())
    if scenario_cross:
        raise ValueError(f"{scenario_cross} scenario groups cross source splits; manual split repair required")
    manifest = []
    for line, row in valid:
        original = row["split"]
        template = text_template(row["text"])
        other = by_template[template]
        if original in {"train", "dev"} and template in gold_templates:
            derived, reason = "excluded", "gold_template_overlap"
        elif original == "train" and ("dev" in other or "test" in other):
            derived, reason = "excluded", "higher_split_template_overlap"
        elif original == "dev" and "test" in other:
            derived, reason = "excluded", "test_template_overlap"
        else:
            derived, reason = original, "retained"
        manifest.append({"utterance_id": row["utterance_id"], "source_line": line,
                         "scenario_id": row["scenario_id"], "original_split": original,
                         "derived_split": derived, "reason": reason,
                         "template_hash": hashlib.sha256(template.encode()).hexdigest()[:16],
                         "language": row["language"], "intent_id": row["primary_intent_id"]})
    kept = defaultdict(set)
    for item in manifest:
        if item["derived_split"] != "excluded":
            kept[item["template_hash"]].add(item["derived_split"])
    if any(len(splits) > 1 for splits in kept.values()):
        raise AssertionError("derived split still has cross-partition templates")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0]))
        writer.writeheader(); writer.writerows(manifest)
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    summary = {"source_rows": len(raw), "usable_rows": len(valid), "invalid_rows": invalid,
               "original_splits": dict(Counter(x["original_split"] for x in manifest)),
               "derived_splits": dict(Counter(x["derived_split"] for x in manifest)),
               "exclusion_reasons": dict(Counter(x["reason"] for x in manifest if x["derived_split"] == "excluded")),
               "language_distribution": dict(Counter(x["language"] for x in manifest)),
               "intent_count": len(labels), "scenario_groups_crossing_source_splits": scenario_cross,
               "template_groups_crossing_source_splits": sum(len(x)>1 for x in by_template.values()),
               "gold_template_count": len(gold_templates), "manifest_sha256": digest,
               "review_status": "all annotated utterances pending human review; gold cases pending legal review",
               "near_duplicate_method": "NFKC casefold + whitespace collapse + digit masking; does not catch every paraphrase"}
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (REPORT_DIR / "nlp_dataset_readiness.md").write_text(
        "# NLP dataset readiness\n\n" + "\n".join(f"- {k}: {v}" for k,v in summary.items() if k != "invalid_rows") +
        "\n\n`AGE` occurs in 26 learner-licence utterances but has no slot-schema row. It is provisional and never inserted into source data.\n"
        "Gold evaluation cases are unreviewed and overlap source texts; they are not an independent benchmark.\n", encoding="utf-8")
    return summary

if __name__ == "__main__":
    print(json.dumps(prepare(), indent=2))
