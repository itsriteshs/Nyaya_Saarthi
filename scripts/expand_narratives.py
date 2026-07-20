#!/usr/bin/env python3
"""Expand narratives.csv with Hindi and realistic challenge variants.

The script is deterministic and keeps the existing English narratives intact.
It uses scenario.csv as the fact source, so new rows do not introduce new
incident facts beyond the source scenario fields.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


FIELDS = [
    "narrative_id",
    "scenario_id",
    "language",
    "script",
    "code_mix_type",
    "narrative_text_original",
    "narrative_text_normalised",
    "variant_type",
    "narrative_completeness",
    "chronology_style",
    "emotionality_level",
    "spelling_noise_level",
    "speech_transcription_style",
    "uncertain_language_present",
    "irrelevant_information_present",
    "reference_date",
    "translation_parent_id",
    "paraphrase_parent_id",
    "source_type",
    "language_reviewer_id",
    "annotation_status",
    "split",
]


ISSUE_HI = {
    "False advertising and misrepresentation": "झूठे विज्ञापन और गलत प्रस्तुति",
    "Noise pollution grievance": "शोर प्रदूषण की शिकायत",
    "Drunk driving accident": "नशे में गाड़ी चलाने से दुर्घटना",
    "Social media hacking": "सोशल मीडिया अकाउंट हैक होना",
    "Medical negligence complaint": "चिकित्सा लापरवाही की शिकायत",
    "Online harassment & threats": "ऑनलाइन उत्पीड़न और धमकी",
    "Safe working conditions violation": "सुरक्षित कार्य-परिस्थितियों का उल्लंघन",
    "Boundary wall dispute": "सीमा दीवार का विवाद",
    "Online banking fraud": "ऑनलाइन बैंकिंग धोखाधड़ी",
    "Ransomware attack": "रैनसमवेयर हमला",
    "Lost phone misuse": "खोए फोन का दुरुपयोग",
    "Hostile workplace intimidation": "कार्यस्थल पर डराना-धमकाना",
    "Chain snatching": "चेन छीनना",
    "Identity theft": "पहचान की चोरी",
    "Cyberstalking": "साइबर पीछा करना",
    "Credit card cloning": "क्रेडिट कार्ड क्लोनिंग",
    "House burglary": "घर में सेंधमारी",
    "Vehicle theft": "वाहन चोरी",
    "Online phishing theft": "ऑनलाइन फिशिंग के जरिए चोरी",
    "Shopbreaking": "दुकान में सेंधमारी",
    "Armed robbery": "हथियार दिखाकर लूट",
    "Physical altercation": "शारीरिक झगड़ा",
    "Verbal intimidation": "मौखिक धमकी",
    "Dowry harassment": "दहेज उत्पीड़न",
    "Domestic dispute": "घरेलू विवाद",
    "Illegal property possession": "संपत्ति पर अवैध कब्जा",
    "Land encroachment": "जमीन पर अतिक्रमण",
    "Tenant-landlord conflict": "किरायेदार-मकान मालिक विवाद",
    "Defective product delivery": "खराब सामान की डिलीवरी",
    "Overcharging and hidden fees": "अधिक शुल्क और छिपे हुए शुल्क",
    "Refusal of service refund": "सेवा का रिफंड देने से इनकार",
    "Expired or contaminated goods sale": "एक्सपायर या दूषित सामान बेचना",
    "Traffic signal violation dispute": "ट्रैफिक सिग्नल उल्लंघन विवाद",
    "Minor civic infrastructure issue": "स्थानीय नागरिक सुविधा की समस्या",
    "Breach of employment contract": "रोजगार अनुबंध का उल्लंघन",
    "Wrongful termination": "गलत तरीके से नौकरी से निकालना",
    "Wage non-payment": "वेतन न देना",
    "Workplace harassment": "कार्यस्थल उत्पीड़न",
    "Restitution of conjugal rights": "वैवाहिक सहवास अधिकार का विवाद",
    "Divorce proceedings conflict": "तलाक प्रक्रिया से जुड़ा विवाद",
    "Alimony and maintenance claim": "भरण-पोषण या गुजारा भत्ता दावा",
    "Inheritance property claim": "विरासत संपत्ति दावा",
    "Guardianship dispute": "अभिभावकत्व विवाद",
}

LOCATION_HI = {
    "Shop": "दुकान",
    "Residential street": "आवासीय गली",
    "Highway": "हाईवे",
    "Online platform": "ऑनलाइन प्लेटफॉर्म",
    "Hospital": "अस्पताल",
    "Workplace": "कार्यस्थल",
    "Plot": "प्लॉट",
    "Mobile app": "मोबाइल ऐप",
    "House": "घर",
    "Parking lot": "पार्किंग स्थल",
    "Apartment": "अपार्टमेंट",
    "Road": "सड़क",
    "Office": "ऑफिस",
    "Showroom": "शोरूम",
    "Alleyway": "गली",
    "Hostel": "हॉस्टल",
    "Kirana store": "किराना दुकान",
    "Marketplace": "बाजार",
    "Railway station": "रेलवे स्टेशन",
    "Restaurant": "रेस्टोरेंट",
    "Construction site": "निर्माण स्थल",
}

STATE_HI = {
    "Delhi": "दिल्ली",
    "Maharashtra": "महाराष्ट्र",
    "Gujarat": "गुजरात",
    "Tamil Nadu": "तमिलनाडु",
    "Telangana": "तेलंगाना",
    "Karnataka": "कर्नाटक",
    "Uttar Pradesh": "उत्तर प्रदेश",
    "West Bengal": "पश्चिम बंगाल",
}

ISSUE_LATIN = {
    "False advertising and misrepresentation": "false advertising aur misrepresentation",
    "Noise pollution grievance": "noise pollution complaint",
    "Drunk driving accident": "drunk driving accident",
    "Social media hacking": "social media hacking",
    "Medical negligence complaint": "medical negligence complaint",
    "Online harassment & threats": "online harassment aur threats",
    "Safe working conditions violation": "safe working conditions violation",
    "Boundary wall dispute": "boundary wall dispute",
    "Online banking fraud": "online banking fraud",
    "Ransomware attack": "ransomware attack",
    "Lost phone misuse": "lost phone ka misuse",
    "Hostile workplace intimidation": "workplace intimidation",
    "Chain snatching": "chain snatching",
    "Identity theft": "identity theft",
    "Cyberstalking": "cyberstalking",
    "Credit card cloning": "credit card cloning",
    "House burglary": "house burglary",
    "Vehicle theft": "vehicle theft",
    "Online phishing theft": "online phishing theft",
    "Shopbreaking": "shopbreaking",
    "Armed robbery": "armed robbery",
    "Physical altercation": "physical altercation",
    "Verbal intimidation": "verbal intimidation",
    "Dowry harassment": "dowry harassment",
    "Domestic dispute": "domestic dispute",
    "Illegal property possession": "illegal property possession",
    "Land encroachment": "land encroachment",
    "Tenant-landlord conflict": "tenant landlord conflict",
    "Defective product delivery": "defective product delivery",
    "Overcharging and hidden fees": "overcharging aur hidden fees",
    "Refusal of service refund": "refund dene se refusal",
    "Expired or contaminated goods sale": "expired ya contaminated goods sale",
    "Traffic signal violation dispute": "traffic signal violation dispute",
    "Minor civic infrastructure issue": "civic infrastructure issue",
    "Breach of employment contract": "employment contract breach",
    "Wrongful termination": "wrongful termination",
    "Wage non-payment": "salary non-payment",
    "Workplace harassment": "workplace harassment",
    "Restitution of conjugal rights": "conjugal rights ka dispute",
    "Divorce proceedings conflict": "divorce proceedings conflict",
    "Alimony and maintenance claim": "maintenance ya alimony claim",
    "Inheritance property claim": "inheritance property claim",
    "Guardianship dispute": "guardianship dispute",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def scenario_num(scenario_id: str) -> str:
    match = re.search(r"(\d+)$", scenario_id)
    return f"{int(match.group(1)):06d}" if match else scenario_id


def flag_hi(value: str, yes: str, no: str) -> str:
    return yes if value == "True" or value == "Yes" else no


def hindi_text(s: dict[str, str]) -> str:
    issue = ISSUE_HI.get(s["secondary_issue_labels"], s["secondary_issue_labels"])
    location = LOCATION_HI.get(s["location_type"], s["location_type"])
    state = STATE_HI.get(s["jurisdiction_state"], s["jurisdiction_state"])
    danger = "इस समय भी खतरा बना हुआ है" if s["current_danger_status"] == "Yes" else "फिलहाल तत्काल खतरे की बात नहीं कही गई है"
    police = "पुलिस से संपर्क किया गया है" if s["police_contacted"] == "True" else "अभी पुलिस से संपर्क नहीं हुआ है"
    legal = "व्यक्ति कानूनी मदद चाहता है" if s["legal_help_requested"] == "True" else "अभी कानूनी मदद स्पष्ट रूप से नहीं मांगी गई है"
    injury = flag_hi(s["injury_present"], "चोट लगने की बात भी बताई गई है", "चोट की स्पष्ट जानकारी नहीं है")
    threat = flag_hi(s["threat_present"], "धमकी या डराने की बात मौजूद है", "धमकी की स्पष्ट बात नहीं है")
    prop = flag_hi(s["property_involved"], "संपत्ति या पैसों से जुड़ा नुकसान बताया गया है", "संपत्ति से जुड़ा नुकसान स्पष्ट नहीं है")
    return norm_text(
        f"मैं यह घटना दर्ज कराना चाहता/चाहती हूं। मामला {issue} से जुड़ा है। "
        f"यह {s['incident_date']} को लगभग {s['incident_time']} बजे {state} में {location} पर हुआ बताया गया है। "
        f"{danger}। {injury}। {threat}। {prop}। {police} और {legal}। "
        f"कुछ बातें अभी पूरी तरह साफ नहीं हैं, इसलिए मूल घटना के तथ्य जैसे बताए गए हैं वैसे ही दर्ज किए जाएं।"
    )


def latin_variant_text(s: dict[str, str], idx: int) -> tuple[str, str, str, str, str]:
    issue = ISSUE_LATIN.get(s["secondary_issue_labels"], s["secondary_issue_labels"].lower())
    location = s["location_type"].lower()
    state = s["jurisdiction_state"]
    police = "police ko bataya hai" if s["police_contacted"] == "True" else "police ko abhi nahi bataya"
    legal = "legal help chahiye" if s["legal_help_requested"] == "True" else "legal help ke baare me sure nahi hu"
    danger = "abhi bhi danger lag raha hai" if s["current_danger_status"] == "Yes" else "abhi immediate danger nahi hai"
    styles = [
        (
            f"Sir please note, {issue} ka matter hai. {s['incident_date']} ko around {s['incident_time']} {location}, {state} me hua. {police}. {legal}. {danger}, but details thode scattered hain.",
            "code_mixed",
            "medium",
            "out_of_order",
            "moderate",
        ),
        (
            f"Main bahut upset hu. {location} par {issue} hua tha, time lagbhag {s['incident_time']} on {s['incident_date']}. Pehle mujhe laga chhota matter hai but ab serious lag raha hai. {police}.",
            "emotional",
            "medium",
            "flashback",
            "high",
        ),
        (
            f"{issue}... {state} me, {location} side. Date maybe {s['incident_date']}, time around {s['incident_time']}. Exact sab yaad nahi but jo hua wahi report karna hai. {legal}.",
            "incomplete",
            "low",
            "fragmented",
            "moderate",
        ),
        (
            f"Actually sequence clear nahi hai: pehle problem notice hui, then {issue} wala incident {s['incident_date']} ko {s['incident_time']} ke aas paas {location} par hua, {state}. {police}; {danger}.",
            "out_of_order",
            "medium",
            "non_linear",
            "moderate",
        ),
        (
            f"plz help, {issue} hua h {location} me {s['incident_date']} {s['incident_time']} ke around. {police}, {legal}, aur mujhe samajh nahi aa rha next kya karu.",
            "noisy",
            "medium",
            "chronological",
            "high",
        ),
    ]
    return styles[idx % len(styles)]


def english_challenge_text(base_text: str, s: dict[str, str], idx: int) -> tuple[str, str, str, str, str]:
    issue = s["secondary_issue_labels"].lower()
    pieces = [
        (
            f"I am not sure I am explaining this in the right order. Around {s['incident_time']} on {s['incident_date']}, the {issue} happened at the {s['location_type'].lower()} in {s['jurisdiction_state']}. I may be missing some details, but I do not want any facts added beyond what I said.",
            "challenge_uncertain",
            "medium",
            "non_linear",
            "moderate",
        ),
        (
            f"Please record this carefully: {base_text} I am emotional right now, so some parts may sound repeated, but the exact scenario anchors are {s['incident_date']}, around {s['incident_time']}, at the {s['location_type'].lower()} in {s['jurisdiction_state']}.",
            "emotional_paraphrase",
            "high",
            "chronological",
            "high",
        ),
        (
            f"{s['location_type']} / {s['jurisdiction_state']} / {s['incident_date']} / about {s['incident_time']}. The issue is {issue}. I have not written a perfect complaint, just the facts I remember.",
            "fragmented_note",
            "low",
            "fragmented",
            "low",
        ),
    ]
    return pieces[idx % len(pieces)]


def make_row(
    narrative_id: str,
    scenario: dict[str, str],
    text: str,
    language: str,
    script: str,
    code_mix_type: str,
    variant_type: str,
    completeness: str,
    chronology: str,
    emotionality: str,
    noise: str,
    translation_parent_id: str,
    paraphrase_parent_id: str,
) -> dict[str, str]:
    return {
        "narrative_id": narrative_id,
        "scenario_id": scenario["scenario_id"],
        "language": language,
        "script": script,
        "code_mix_type": code_mix_type,
        "narrative_text_original": text,
        "narrative_text_normalised": norm_text(text),
        "variant_type": variant_type,
        "narrative_completeness": completeness,
        "chronology_style": chronology,
        "emotionality_level": emotionality,
        "spelling_noise_level": noise,
        "speech_transcription_style": "False",
        "uncertain_language_present": "True" if completeness == "low" or "uncertain" in variant_type else "False",
        "irrelevant_information_present": "False",
        "reference_date": scenario["reference_date"],
        "translation_parent_id": translation_parent_id,
        "paraphrase_parent_id": paraphrase_parent_id,
        "source_type": "synthetic_pending_review",
        "language_reviewer_id": "",
        "annotation_status": "pending_review",
        "split": scenario["split"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="scenario.csv")
    parser.add_argument("--narratives", default="narratives.csv")
    parser.add_argument("--additional", type=int, default=300)
    args = parser.parse_args()

    scenarios = read_csv(Path(args.scenario))
    original_rows = read_csv(Path(args.narratives))
    if not original_rows:
        raise SystemExit("narratives.csv is empty")

    if list(original_rows[0].keys()) != FIELDS:
        raise SystemExit("narratives.csv schema does not match expected fields")

    english_by_scenario: dict[str, dict[str, str]] = {}
    retained: list[dict[str, str]] = []
    for row in original_rows:
        if row["language"] == "en" and row["scenario_id"] not in english_by_scenario:
            english_by_scenario[row["scenario_id"]] = row
            retained.append(row)

    missing = [s["scenario_id"] for s in scenarios if s["scenario_id"] not in english_by_scenario]
    if missing:
        raise SystemExit(f"Missing English narrative for scenarios: {missing[:10]}")

    rows = list(retained)
    existing_ids = {r["narrative_id"] for r in rows}

    for scenario in scenarios:
        parent_id = english_by_scenario[scenario["scenario_id"]]["narrative_id"]
        nid = f"NAR{scenario_num(scenario['scenario_id'])}_HI"
        if nid in existing_ids:
            continue
        rows.append(
            make_row(
                nid,
                scenario,
                hindi_text(scenario),
                "hi",
                "Devanagari",
                "none",
                "natural_translation",
                "medium",
                "chronological",
                "moderate",
                "none",
                parent_id,
                "",
            )
        )
        existing_ids.add(nid)

    selected = scenarios[: args.additional]
    for idx, scenario in enumerate(selected):
        parent = english_by_scenario[scenario["scenario_id"]]
        suffix = "HILATN" if idx % 2 == 0 else "ENVAR"
        nid = f"NAR{scenario_num(scenario['scenario_id'])}_{suffix}"
        if idx % 2 == 0:
            text, variant, completeness, chronology, emotion = latin_variant_text(scenario, idx)
            language, script, code_mix, noise = "hi-Latn", "Latin", "Hinglish", "medium" if variant == "noisy" else "low"
        else:
            text, variant, completeness, chronology, emotion = english_challenge_text(
                parent["narrative_text_original"], scenario, idx
            )
            language, script, code_mix, noise = "en", "Latin", "none", "low"
        rows.append(
            make_row(
                nid,
                scenario,
                text,
                language,
                script,
                code_mix,
                variant,
                completeness,
                chronology,
                emotion,
                noise,
                "",
                parent["narrative_id"],
            )
        )

    write_csv(Path(args.narratives), rows)
    print(f"Wrote {len(rows)} narrative rows: {len(retained)} retained English, {len(scenarios)} Hindi, {len(selected)} additional variants.")


if __name__ == "__main__":
    main()
