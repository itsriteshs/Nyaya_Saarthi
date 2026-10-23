"""Transparent LIME-style token deletion surrogate on real SVM margins.
No probability conversion; perturbations are word-position presence masks.
"""
import re
import time
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

def explain(model,text,samples=300,seed=471):
    tokens=re.findall(r"\S+",text)
    if len(tokens)<2: return {"status":"abstained","reason":"At least two whitespace tokens required"}
    started=time.perf_counter();rng=np.random.default_rng(seed)
    masks=rng.integers(0,2,size=(samples+100,len(tokens)));masks[0]=1
    sentences=[" ".join(t for t,on in zip(tokens,m) if on) for m in masks]
    scores=np.asarray(model.decision_function(sentences))
    if scores.ndim==1:scores=np.column_stack([-scores,scores])
    distance=1-np.sqrt(masks.mean(axis=1))
    weights=np.exp(-(distance/.25)**2)
    surrogate=Ridge(alpha=1.0).fit(masks[:samples],scores[:samples],sample_weight=weights[:samples])
    predicted=surrogate.predict(masks);winner=int(scores[0].argmax())
    terms=sorted([{"position":i,"token":t,"weight":float(surrogate.coef_[winner,i])} for i,t in enumerate(tokens)],key=lambda t:-abs(t["weight"]))
    return {"status":"measured","method":"LIME-style weighted Ridge token deletion; SVM decision margins",
            "seed":seed,"perturbations":samples,"heldOutPerturbations":100,"kernelWidth":.25,"ridgeAlpha":1.0,
            "predictedIntent":str(model.classes_[winner]),"tokens":terms,
            "trainingR2":float(r2_score(scores[:samples,winner],predicted[:samples,winner],sample_weight=weights[:samples])),
            "heldOutR2":float(r2_score(scores[samples:,winner],predicted[samples:,winner],sample_weight=weights[samples:])),
            "heldOutAgreement":float(np.mean(scores[samples:].argmax(axis=1)==predicted[samples:].argmax(axis=1))),
            "originalMargin":float(scores[0,winner]),"surrogateOriginalMargin":float(predicted[0,winner]),
            "latencyMs":round((time.perf_counter()-started)*1000),
            "limitation":"Local model behavior under artificial deletions; not causal, legal evidence, or calibrated probability. Negative held-out R2 is possible."}
