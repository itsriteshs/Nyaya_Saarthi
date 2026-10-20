"""Materialize reversible structural research corrections outside source data.

The overlay is not a legally reviewed production dataset.
"""
import argparse
import csv
import json
import shutil
from pathlib import Path
from app.config import DATASET_DIR


def materialize(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    for source in DATASET_DIR.iterdir():
        if source.is_file(): shutil.copy2(source, destination / source.name)
    path = destination / "procedures.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream: rows = list(csv.reader(stream))
    header = rows[0]
    target = next((i for i, row in enumerate(rows[1:], 1) if row and row[0] == "PROC_CONTEST_ECHALLAN_COURT"), None)
    if target is None: raise ValueError("Expected procedure record is missing")
    original = rows[target][:]
    if len(original) != len(header) - 1 or original[13] != "Court filing fee (nominal, State-specific)" or original[17] != "SRC_MVAA_2019":
        raise ValueError("Expected unambiguous column shift was not found")
    rows[target].insert(13, "")
    assert len(rows[target]) == len(header) and rows[target][14] == original[13] and rows[target][18] == original[17]
    with path.open("w", encoding="utf-8-sig", newline="") as stream: csv.writer(stream).writerows(rows)
    slot_path = destination / "slot_schema.csv"
    with slot_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        slots = list(reader)
    if any(row["slot_name"] == "AGE" and row["intent_id"] == "INT016" for row in slots):
        raise ValueError("AGE already exists; inspect source changes")
    provisional = dict.fromkeys(fields, "")
    provisional.update({"slot_id": "PHASE6_PROVISIONAL_AGE", "intent_id": "INT016", "slot_name": "AGE",
                        "slot_display_name": "Age", "slot_description": "Provisional learner-licence age context; annotation-supported, not legal-review approved.",
                        "data_type": "integer", "required_level": "conditional",
                        "required_when_json": json.dumps({"when": "only_when_relevant_to_rule_or_situation"}),
                        "ask_priority": "5", "why_legally_relevant": "Age may affect learner-licence context; exact legal condition awaits review.",
                        "question_template_en": "How old was the person at the time of the event?",
                        "question_template_hi": "घटना के समय व्यक्ति की उम्र कितनी थी?",
                        "question_template_hinglish": "Ghatna ke samay vyakti ki age kitni thi?",
                        "normalization_rule": "Keep explicit age only; do not infer.", "maps_to_rule_field": "age"})
    slots.append(provisional)
    with slot_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(slots)
    change_log = {"sourceDatasetUnchanged": True, "overlay": str(destination),
                  "changes": [{"file": "procedures.csv", "record": original[0], "action": "insert empty deadline field at column 13",
                               "basis": "The next value is explicitly a court filing fee, and every later typed field aligns after insertion.",
                               "originalRow": original, "repairedRow": rows[target]},
                              {"file": "slot_schema.csv", "record": "PHASE6_PROVISIONAL_AGE", "action": "append conditional schema row",
                               "basis": "INT016 names AGE; 26 annotations contain AGE. Legal triggering condition remains unimplemented."}],
                  "unresolved": ["OFF_NO_PUC.source_id is empty and cannot be inferred.",
                                 "The repaired procedure remains NOT_VERIFIED and is not admissible legal guidance."]}
    (destination / "phase6_overlay_change_log.json").write_text(json.dumps(change_log, indent=2, ensure_ascii=False), encoding="utf-8")
    return change_log


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path, help="Directory outside the source Dataset 2 folder")
    args = parser.parse_args()
    if args.destination.resolve() == DATASET_DIR.resolve(): parser.error("source dataset cannot be overwritten")
    result = materialize(args.destination)
    print(json.dumps({"overlay": result["overlay"], "changes": [x["record"] for x in result["changes"]],
                      "remaining": result["unresolved"]}, indent=2))
