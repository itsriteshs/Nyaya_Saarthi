#!/usr/bin/env python3
"""Rebuild classifications.csv so every narrative has one classification."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


FIELDS = [
    "classification_id",
    "narrative_id",
    "primary_category",
    "secondary_categories",
    "procedural_intents",
    "user_goal",
    "urgency_class",
    "current_danger",
    "ongoing_incident",
    "medical_emergency",
    "incident_medium",
    "current_or_past",
    "property_involved",
    "threat_involved",
    "injury_involved",
    "weapon_mentioned",
    "minor_involved",
    "police_already_contacted",
    "legal_aid_requested",
    "recommended_route",
    "annotator_1_label",
    "annotator_2_label",
    "adjudicated_label",
    "reviewer_id",
]


SECONDARY_EXTRAS = {
    "Consumer Disputes": "consumer_grievance",
    "Miscellaneous": "civic_or_public_safety",
    "Traffic & Road Incidents": "traffic_or_road_safety",
    "Cybercrime": "digital_platform_incident",
    "Financial Fraud": "financial_loss_or_fraud",
    "Assault & Threats": "personal_safety",
    "Domestic Violence": "domestic_safety",
    "Theft and robbery": "property_loss",
    "Property Disputes": "property_conflict",
    "Employment/Labour": "workplace_rights",
    "Family Law": "family_legal_support",
}


USER_GOALS = {
    "Consumer Disputes": "prepare a consumer complaint and identify refund or service remedies",
    "Miscellaneous": "prepare a civic complaint and identify the right authority",
    "Traffic & Road Incidents": "document the road incident and understand reporting options",
    "Cybercrime": "prepare a cybercrime report and preserve digital evidence",
    "Financial Fraud": "report financial fraud and preserve transaction evidence",
    "Assault & Threats": "document the threat or assault and understand police reporting options",
    "Domestic Violence": "seek safety-focused help and prepare a support or complaint record",
    "Theft and robbery": "prepare a theft or robbery complaint and list lost property",
    "Property Disputes": "organise property-dispute facts and identify documentation gaps",
    "Employment/Labour": "prepare a workplace rights complaint or legal-aid intake",
    "Family Law": "organise family-law facts and identify support options",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def bool_text(value: str) -> str:
    return "True" if value in {"True", "Yes", "true", "yes"} else "False"


def incident_medium(setting: str) -> str:
    mapping = {"Physical": "physical", "Online": "online", "Hybrid": "hybrid"}
    return mapping.get(setting, "unknown")


def current_or_past(value: str) -> str:
    mapping = {"ongoing": "current", "recent_past": "recent", "past": "past"}
    return mapping.get(value, "unknown")


def contains_any(text: str, terms: list[str]) -> bool:
    low = text.lower()
    return any(term in low for term in terms)


def secondary_categories(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    labels = [scenario["secondary_issue_labels"]]
    extra = SECONDARY_EXTRAS.get(scenario["primary_incident_family"])
    if extra:
        labels.append(extra)
    if narrative["uncertain_language_present"] == "True":
        labels.append("uncertain_or_incomplete_user_account")
    if narrative["chronology_style"] in {"fragmented", "non_linear", "out_of_order", "flashback"}:
        labels.append("timeline_reconstruction_needed")
    return ";".join(dict.fromkeys(labels))


def procedural_intents(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    family = scenario["primary_incident_family"]
    intents: list[str] = []
    if scenario["current_danger_status"] == "Yes":
        intents.append("safety_triage")
    if scenario["police_contacted"] == "False" and family in {
        "Cybercrime",
        "Financial Fraud",
        "Assault & Threats",
        "Domestic Violence",
        "Theft and robbery",
        "Traffic & Road Incidents",
    }:
        intents.append("reporting_guidance")
    if scenario["police_contacted"] == "True":
        intents.append("complaint_followup")
    if family in {"Consumer Disputes", "Employment/Labour", "Property Disputes", "Family Law", "Miscellaneous"}:
        intents.append("legal_navigation")
    if scenario["property_involved"] == "True" or family in {"Cybercrime", "Financial Fraud"}:
        intents.append("evidence_preservation")
    if narrative["narrative_completeness"] == "low" or narrative["uncertain_language_present"] == "True":
        intents.append("clarification_needed")
    if not intents:
        intents.append("case_preparation")
    return ";".join(dict.fromkeys(intents))


def urgency_class(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    text = narrative["narrative_text_original"]
    if scenario["current_danger_status"] == "Yes":
        return "emergency_current_danger"
    if scenario["injury_present"] == "True" and contains_any(text, ["hospital", "medical", "injury", "चोट", "अस्पताल"]):
        return "medical_attention_needed"
    if scenario["threat_present"] == "True" and scenario["ongoing_or_past"] == "ongoing":
        return "ongoing_threat"
    if scenario["police_contacted"] == "False" and scenario["primary_incident_family"] in {
        "Cybercrime",
        "Financial Fraud",
        "Assault & Threats",
        "Domestic Violence",
        "Theft and robbery",
    }:
        return "reporting_time_sensitive"
    if scenario["legal_help_requested"] == "True":
        return "legal_aid_or_process_help"
    if narrative["narrative_completeness"] == "low":
        return "needs_clarification"
    return "case_preparation"


def recommended_route(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    family = scenario["primary_incident_family"]
    if scenario["current_danger_status"] == "Yes":
        return "safety_redirect_and_case_intake"
    if family == "Cybercrime":
        return "cybercrime_report_preparation"
    if family == "Financial Fraud":
        return "financial_fraud_report_preparation"
    if family in {"Assault & Threats", "Domestic Violence", "Theft and robbery"}:
        return "police_complaint_preparation"
    if family == "Traffic & Road Incidents":
        return "traffic_incident_documentation"
    if family == "Consumer Disputes":
        return "consumer_grievance_preparation"
    if family == "Employment/Labour":
        return "labour_or_workplace_intake"
    if family == "Property Disputes":
        return "property_document_review_intake"
    if family == "Family Law":
        return "family_legal_aid_intake"
    return "general_legal_navigation"


def weapon_mentioned(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    text = f"{scenario['scenario_facts']} {narrative['narrative_text_original']}".lower()
    return "True" if contains_any(text, ["knife", "gun", "weapon", "armed", "हथियार", "चाकू", "बंदूक"]) else "False"


def minor_involved(scenario: dict[str, str], narrative: dict[str, str]) -> str:
    text = f"{scenario['scenario_facts']} {narrative['narrative_text_original']}".lower()
    if contains_any(text, ["minor", "child", "children", "school student", "बच्चा", "नाबालिग"]):
        return "true"
    return "unknown"


def classification_id(index: int) -> str:
    return f"CLS{index:06d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="scenario.csv")
    parser.add_argument("--narratives", default="narratives.csv")
    parser.add_argument("--classifications", default="classifications.csv")
    args = parser.parse_args()

    scenarios = {row["scenario_id"]: row for row in read_csv(Path(args.scenario))}
    narratives = read_csv(Path(args.narratives))
    rows: list[dict[str, str]] = []

    def sort_key(row: dict[str, str]) -> tuple[int, str]:
        match = re.search(r"(\d+)", row["narrative_id"])
        return (int(match.group(1)) if match else 999999, row["narrative_id"])

    for idx, narrative in enumerate(sorted(narratives, key=sort_key), start=1):
        scenario = scenarios[narrative["scenario_id"]]
        primary = scenario["primary_incident_family"]
        current_danger = bool_text(scenario["current_danger_status"])
        ongoing = "True" if scenario["ongoing_or_past"] == "ongoing" else "False"
        rows.append(
            {
                "classification_id": classification_id(idx),
                "narrative_id": narrative["narrative_id"],
                "primary_category": primary,
                "secondary_categories": secondary_categories(scenario, narrative),
                "procedural_intents": procedural_intents(scenario, narrative),
                "user_goal": USER_GOALS.get(primary, "prepare an incident record and identify next steps"),
                "urgency_class": urgency_class(scenario, narrative),
                "current_danger": current_danger,
                "ongoing_incident": ongoing,
                "medical_emergency": "True" if urgency_class(scenario, narrative) == "medical_attention_needed" else "False",
                "incident_medium": incident_medium(scenario["incident_setting"]),
                "current_or_past": current_or_past(scenario["ongoing_or_past"]),
                "property_involved": bool_text(scenario["property_involved"]),
                "threat_involved": bool_text(scenario["threat_present"]),
                "injury_involved": bool_text(scenario["injury_present"]),
                "weapon_mentioned": weapon_mentioned(scenario, narrative),
                "minor_involved": minor_involved(scenario, narrative),
                "police_already_contacted": bool_text(scenario["police_contacted"]),
                "legal_aid_requested": bool_text(scenario["legal_help_requested"]),
                "recommended_route": recommended_route(scenario, narrative),
                "annotator_1_label": primary,
                "annotator_2_label": "",
                "adjudicated_label": primary,
                "reviewer_id": "",
            }
        )

    write_csv(Path(args.classifications), rows)
    print(f"Wrote {len(rows)} classifications for {len(narratives)} narratives.")


if __name__ == "__main__":
    main()
