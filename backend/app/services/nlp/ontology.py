"""Cached read-only NLP vocabularies from project CSVs."""
from functools import lru_cache
from app.config import DATASET_DIR
from app.services.dataset_loader import load_dataset

@lru_cache(maxsize=1)
def ontology():
    def rows(name):
        return [row for _,row in load_dataset(DATASET_DIR / name)[1]
                if isinstance(row,dict) and '__parse_error__' not in row and '__column_error__' not in row]
    intents={r['intent_id']:r for r in rows('intents.csv')}
    slots={}
    for row in rows('slot_schema.csv'):
        slots.setdefault(row['intent_id'],[]).append(row)
    return {"intents":intents,"slots":slots,
            "vehicles":{r['vehicle_class_id']:r for r in rows('vehicle_classes.csv')},
            "jurisdictions":{r['jurisdiction_id']:r for r in rows('jurisdictions.csv')}}
