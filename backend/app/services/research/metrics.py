"""Small denominator-explicit metrics shared by offline experiments."""
import math
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

def ratio(a,b):
    return a/b if b else None

def prf(tp,fp,fn):
    return {"tp":tp,"fp":fp,"fn":fn,"precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn),
            "f1":ratio(2*tp,2*tp+fp+fn)}

def wilson(success,total):
    if not total: return None
    z=1.96; p=success/total; d=1+z*z/total
    c=(p+z*z/(2*total))/d
    r=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [c-r,c+r]

def classification(gold,pred):
    labels=sorted(set(gold)|set(pred))
    correct=sum(a==b for a,b in zip(gold,pred))
    return {"n":len(gold),"accuracy":float(accuracy_score(gold,pred)),
            "accuracy95Wilson":wilson(correct,len(gold)),
            "macroF1":float(f1_score(gold,pred,average="macro",zero_division=0)),
            "perClass":classification_report(gold,pred,output_dict=True,zero_division=0),
            "labels":labels,"confusionMatrix":confusion_matrix(gold,pred,labels=labels).tolist()}

def paired_delta(baseline,variant,seed=471):
    diff=np.array(variant,dtype=float)-np.array(baseline,dtype=float)
    if not len(diff): return None
    rng=np.random.default_rng(seed)
    samples=[float(rng.choice(diff,len(diff),replace=True).mean()) for _ in range(1000)]
    return {"absolute":float(diff.mean()),"pairedBootstrap95":np.quantile(samples,[.025,.975]).tolist(),
            "resamples":1000,"seed":seed,"unit":"case; template dependence may narrow intervals"}
