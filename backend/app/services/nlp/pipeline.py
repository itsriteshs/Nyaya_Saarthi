"""Unified real NLP inference; no legal applicability or guidance claims."""
from datetime import datetime
from app.schemas.nlp import AnalyzeResponse
from app.services.nlp.preprocessing import normalize_text
from app.services.nlp.language import analyze_language
from app.services.nlp.intent_classifier import classify
from app.services.nlp.entity_extractor import extract
from app.services.nlp.normalizer import normalize
from app.services.nlp.slot_detector import detect_slots

def analyze(text: str, requested_language: str='auto', reference_datetime: datetime | None=None) -> AnalyzeResponse:
    normalized=normalize_text(text)
    language=analyze_language(text,requested_language)
    intent=classify(normalized)
    entities=[normalize(e) for e in extract(text,reference_datetime)]
    slots=detect_slots(intent['id'],entities)
    warnings=[]
    if intent['needsClarification']:warnings.append('Intent classifier is uncertain; review alternatives before relying on the selected intent.')
    if language['detectedLanguage']=='uncertain':warnings.append('Language could not be identified confidently.')
    if slots['unresolvedSlots']:warnings.append('Some conditional slot requirements could not be resolved in Phase 2.')
    if any(e['status']=='ambiguous' for e in entities):warnings.append('Some extracted facts need user confirmation.')
    return AnalyzeResponse.model_validate({'inputText':text,'normalizedText':normalized,'language':language,
        'intent':intent,'entities':entities,**slots,'warnings':warnings,'modelVersion':intent['modelVersion']})
