"""Trained TF-IDF intent model. Decision gaps are not probabilities."""
import json
from functools import lru_cache
import joblib
import numpy as np
from app.config import BACKEND_DIR
from app.services.nlp.ontology import ontology
from app.services.nlp.entity_extractor import unitless_speed_matches

ARTIFACT=BACKEND_DIR/'artifacts'/'intent_model.joblib'
METADATA=BACKEND_DIR/'artifacts'/'intent_model_metadata.json'

@lru_cache(maxsize=1)
def load_intent_model():
    if not ARTIFACT.is_file() or not METADATA.is_file():
        raise FileNotFoundError('Train the intent baseline before inference')
    return joblib.load(ARTIFACT),json.loads(METADATA.read_text(encoding='utf-8'))

def classify(text: str):
    model,meta=load_intent_model()
    scores=np.asarray(model.decision_function([text]))[0]
    classes=np.asarray(model.classes_)
    order=np.argsort(scores)[::-1]
    top,runner=int(order[0]),int(order[1])
    gap=float(scores[top]-scores[runner])
    explicit_speed=bool(unitless_speed_matches(text))
    if explicit_speed and str(classes[top])!='INT002':
        top=int(np.where(classes=='INT002')[0][0])
        gap=float(scores[top]-scores[int(order[0])])
    intent_id=str(classes[top]); row=ontology()['intents'][intent_id]
    alternatives=[]
    for rank in (rank for rank in order if int(rank)!=top):
        item=ontology()['intents'][str(classes[rank])]
        alternatives.append({'id':str(classes[rank]),'name':item['intent_name'],
                             'score':round(float(scores[rank]),4)})
        if len(alternatives)==3:break
    return {'id':intent_id,'name':row['intent_name'],'domain':row['domain'],
            'score':round(float(scores[top]),4),'scoreType':
            'Explicit speed phrase rule; SVM score is not probability' if explicit_speed else meta['score_type'],
            'marginGap':round(gap,4),'alternatives':alternatives,
            'needsClarification':True if explicit_speed else gap<meta['uncertainty_gap_threshold'],
            'modelVersion':meta['model_version']}
