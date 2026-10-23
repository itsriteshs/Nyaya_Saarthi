"""Catalog-based normalization of SLM spans, never phrase-based extraction."""
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
import unicodedata
from app.services.nlp.ontology import ontology


def current_reference():
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def state_candidate(value):
    def key(text):
        return ''.join(c for c in unicodedata.normalize('NFKC', text).casefold() if c.isalpha())
    value = key(value)
    if len(value) < 5:
        return None
    ranked = sorted(((SequenceMatcher(None, value, key(r['state_ut_name'])).ratio(), r)
                     for r in ontology()['jurisdictions'].values() if r['jurisdiction_level'] != 'CENTRAL'),
                    key=lambda x: x[0], reverse=True)
    if ranked and ranked[0][0] >= .88 and (len(ranked)==1 or ranked[0][0]-ranked[1][0] >= .08):
        return ranked[0][1]
    return None
