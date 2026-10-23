"""Inspectable linear features, captured at inference; never chain-of-thought."""
import hashlib
from functools import lru_cache
import numpy as np
from app.services.nlp.intent_classifier import ARTIFACT

def linear_attribution(model, text, limit=12):
    vectorizer, classifier = model.steps[0][1], model.steps[-1][1]
    x = vectorizer.transform([text]).tocsr()
    scores = np.asarray(model.decision_function([text]))[0]
    if np.ndim(scores) == 0:
        scores = np.array([-float(scores), float(scores)])
        coefficients = np.vstack([-classifier.coef_[0], classifier.coef_[0]])
        intercepts = np.array([-classifier.intercept_[0], classifier.intercept_[0]])
    else:
        coefficients, intercepts = classifier.coef_, classifier.intercept_
    order = np.argsort(scores)[::-1]
    names = vectorizer.get_feature_names_out()
    result = []
    for index in order[:3]:
        contributions = [(str(names[j]), float(v * coefficients[index, j]))
                         for j, v in zip(x.indices, x.data)]
        positive = sorted((v for v in contributions if v[1] > 0), key=lambda v: -v[1])[:limit]
        negative = sorted((v for v in contributions if v[1] < 0), key=lambda v: v[1])[:limit]
        result.append({"intent": str(classifier.classes_[index]), "score": float(scores[index]),
                       "intercept": float(intercepts[index]), "allFeatureSum": sum(v for _, v in contributions),
                       "positive": [{"feature": n, "contribution": v} for n,v in positive],
                       "negative": [{"feature": n, "contribution": v} for n,v in negative]})
    return {"method": "TF-IDF value × fitted LinearSVC coefficient", "scoreType": "decision margin, not probability",
            "input": text, "classes": result, "marginGap": float(scores[order[0]]-scores[order[1]]),
            "limitation": "Character n-gram contributions are model features, not causal proof; only top signed features shown."}

@lru_cache(maxsize=1)
def artifact_hash():
    return hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()

def capture(model, text):
    result = linear_attribution(model, text)
    result["artifactSHA256"] = artifact_hash()
    return result
