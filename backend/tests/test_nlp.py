"""Phase 2 tests against locally trained artifacts and repository datasets."""
from datetime import datetime, timezone

from app.services.nlp.preprocessing import normalize_text
from app.services.nlp.language import analyze_language
from app.services.nlp.pipeline import analyze
from app.services.nlp.entity_extractor import extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.slot_detector import detect_slots


def test_preprocessing_preserves_meaning_and_original_spans():
    source = "  मैंने 120 km/h चलाया; I do not have insurance.  "
    normalized = normalize_text(source)
    assert "120 km/h" in normalized and "मैंने" in normalized and "not" in normalized
    entities = extract(source)
    assert all(source[item["start"]:item["end"]] == item["text"] for item in entities)


def test_language_script_and_uncertainty():
    assert analyze_language("तेज गाड़ी चलाने पर चालान मिला", "auto")["detectedLanguage"] == "hindi"
    assert analyze_language("Meri car का चालान", "english")["detectedLanguage"] == "mixed"
    assert analyze_language("मेरी कार का insurance खत्म हो गया", "auto")["detectedLanguage"] == "hindi"
    assert analyze_language("hi", "auto")["detectedLanguage"] == "uncertain"
    assert analyze_language("Mera speeding ka challan kat gaya", "auto")["detectedLanguage"] in {"hinglish", "uncertain"}
    assert analyze_language("I received a speeding challan", "auto")["detectedLanguage"] in {"english", "uncertain"}


def test_intent_baseline_returns_ontology_ids_and_alternatives():
    cases = {
        "I got a speeding challan": "INT002",
        "How do I challenge a challan?": "INT045",
        "Can I renew my licence?": "INT018",
        "My insurance expired": "INT032",
    }
    for sentence, expected in cases.items():
        result = analyze(sentence)
        assert result.intent.id == expected
        assert result.intent.scoreType.lower().find("probability") >= 0
        assert result.intent.alternatives
    multiple = analyze("My insurance expired and I got a speeding challan")
    assert multiple.intent.alternatives


def test_entities_and_grounded_normalization():
    text = "About 120 kmph in my car on an expressway in Tamilnadu yesterday"
    reference = datetime(2026, 10, 19, tzinfo=timezone.utc)
    entities = [normalize(item) for item in extract(text, reference)]
    by_type = {item["type"]: item for item in entities}
    assert by_type["OBSERVED_SPEED"]["normalizedValue"] == "120"
    assert by_type["OBSERVED_SPEED"]["approximate"] is True
    assert by_type["VEHICLE_CLASS"]["normalizedId"] == "VC_MOTORCAR"
    assert by_type["STATE"]["normalizedValue"] == "Tamil Nadu"
    assert by_type["ROAD_TYPE"]["status"] == "resolved"
    assert by_type["EVENT_DATE"]["normalizedValue"] == "2026-10-18"
    assert all(text[e["start"]:e["end"]] == e["text"] for e in entities)
    assert not [e for e in extract("My challan number is 120") if e["type"] == "OBSERVED_SPEED"]
    assert normalize(next(e for e in extract("bike") if e["type"] == "VEHICLE_CLASS"))["status"] == "ambiguous"


def test_status_negation_and_age_gap():
    yes = [normalize(e) for e in extract("I received a challan")]
    no = [normalize(e) for e in extract("I did not receive a challan")]
    assert any(e["type"] == "CHALLAN_STATUS" and e["normalizedValue"] == "absent" for e in no)
    assert any(e["type"] == "CHALLAN_STATUS" for e in yes)
    assert any(e["type"] == "AGE" for e in extract("My age: 17"))
    assert any(s["slot"] == "AGE" and s["reason"] == "provisional_schema_gap" for s in detect_slots("INT016", [] )["unresolvedSlots"])


def test_status_phrase_vocabulary_uses_only_allowed_training_rows(monkeypatch):
    from app.services.nlp import entity_extractor
    rows = [(2, {"utterance_id": "train", "entity_annotations_json": '[{"slot_name":"INSURANCE_STATUS","value":"active policy"}]'}),
            (3, {"utterance_id": "test", "entity_annotations_json": '[{"slot_name":"INSURANCE_STATUS","value":"held out phrase"}]'})]
    monkeypatch.setattr(entity_extractor, "load_dataset", lambda _: ([], rows))
    vocab = entity_extractor.build_status_vocabulary({"train"})
    assert "active policy" in vocab["INSURANCE_STATUS"]
    assert "held out phrase" not in vocab["INSURANCE_STATUS"]


def test_slot_requirements_are_intent_specific():
    empty = detect_slots("INT002", [])
    assert empty["missingSlots"] and empty["readiness"]["percentage"] < 100
    assert empty["readiness"]["status"] == "needs_context"
    filled = [normalize(e) for e in extract("car 120 km/h expressway Tamil Nadu")]
    partial = detect_slots("INT002", filled)
    assert partial["readiness"]["found"] > empty["readiness"]["found"]
    assert partial["unresolvedSlots"]


def test_nlp_endpoint_validation_and_real_artifact(client, monkeypatch):
    url = "/api/v1/nlp/analyze"
    for payload in ({"text": ""}, {"text": "x" * 20001}, {"text": "hello", "language": "invalid"}):
        assert client.post(url, json=payload).status_code == 422
    response = client.post(url, json={"text": "I drove my car at 120 km/h in Tamil Nadu", "language": "auto"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["intent"]["id"].startswith("INT")
    assert body["entities"] and body["modelVersion"]
    assert body["language"]["requestedLanguage"] == "auto"
    from app.services.nlp import intent_classifier
    monkeypatch.setattr(intent_classifier, "ARTIFACT", intent_classifier.ARTIFACT.with_name("absent.joblib"))
    intent_classifier.load_intent_model.cache_clear()
    assert client.post(url, json={"text": "Speeding"}).status_code == 503
    intent_classifier.load_intent_model.cache_clear()


def test_matter_analysis_create_retrieve_and_conflict(client):
    text = "I drove my car at 120 km/h in Tamil Nadu"
    created = client.post("/api/v1/matters", json={"originalText": text, "language": "auto"}).json()
    url = f"/api/v1/matters/{created['id']}"
    analyzed = client.post(url + "/analyze", json={"revision": created["revision"]})
    assert analyzed.status_code == 200, analyzed.text
    matter = analyzed.json()
    assert matter["revision"] == 2
    assert matter["originalText"] == text
    assert matter["nlpAnalysis"]["entities"]
    assert any(fact["requiresConfirmation"] and not fact["confirmed"] for fact in matter["facts"])
    if matter['nlpAnalysis']['intent']['needsClarification']:
        assert matter['missingSlots']==['INTENT']
        assert matter['currentQuestion']['slot']=='INTENT'
        assert {item['slot'] for item in matter['nlpAnalysis']['missingSlots']}=={'ROAD_TYPE'}
    else:
        assert set(matter['missingSlots']) == {item['slot'] for item in matter['nlpAnalysis']['missingSlots']}
    assert client.get(url).json()["nlpAnalysis"] == matter["nlpAnalysis"]
    assert client.post(url + "/analyze", json={"revision": 1}).status_code == 409
    assert client.post(url + "/analyze", json={"revision": 2}).status_code == 409
