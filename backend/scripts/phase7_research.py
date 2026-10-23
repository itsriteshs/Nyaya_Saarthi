"""Development-only offline research. Immutable run directory; never writes Phase 6."""
import argparse
import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.research.metrics import classification, paired_delta, ratio, prf, wilson

ROOT=BACKEND_DIR/"experiments"
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value): path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding="utf-8")
def nlp(out):
    from app.services.nlp.preprocessing import normalize_text
    from app.services.nlp.language import analyze_language, load_language_model
    from app.services.nlp.entity_extractor import extract, build_status_vocabulary
    from app.services.nlp.normalizer import normalize
    manifest=ROOT/"manifests/phase6_grouped_split.csv"
    assignment={r["utterance_id"]:r["split"] for r in csv.DictReader(manifest.open(encoding="utf-8"))}
    dataset=DATASET_DIR/"annotated_utterances.csv"
    rows=[r for r in csv.DictReader(dataset.open(encoding="utf-8-sig")) if assignment.get(r["utterance_id"]) in {"train","dev"}]
    train=[r for r in rows if assignment[r["utterance_id"]]=="train"]
    dev=[r for r in rows if assignment[r["utterance_id"]]=="dev"]
    x=[normalize_text(r["text"]) for r in train]; y=[r["primary_intent_id"] for r in train]
    xd=[normalize_text(r["text"]) for r in dev]; gold=[r["primary_intent_id"] for r in dev]
    predictions={}; scores={}
    for name,estimator in [("linear_svc",LinearSVC(random_state=471)),("logistic_regression",LogisticRegression(max_iter=1000,random_state=471))]:
        model=Pipeline([("tfidf",TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),min_df=2,max_features=100000)),("classifier",estimator)])
        model.fit(x,y)
        predictions[name]=model.predict(xd).tolist()
        scores[name]=classification(gold,predictions[name])
    from app.services.nlp.intent_classifier import load_intent_model
    runtime,meta=load_intent_model()
    predictions["production_svc"]=runtime.predict(xd).tolist()
    scores["production_svc"]=classification(gold,predictions["production_svc"])
    margins=runtime.decision_function(xd); gaps=np.sort(margins,axis=1)[:,-1]-np.sort(margins,axis=1)[:,-2]
    scores["production_svc"]["uncertainRate"]=float(np.mean(gaps<meta["uncertainty_gap_threshold"]))
    scores["production_svc"]["threshold"]=meta["uncertainty_gap_threshold"]
    language_model,_=load_language_model()
    lang_gold=[r["language"].lower() for r in dev]
    lang_raw=[str(v).lower() for v in language_model.predict(xd)]
    lang_policy=[analyze_language(r["text"],"auto")["detectedLanguage"] for r in dev]
    languages={}
    for name,pred in [("raw_classifier",lang_raw),("script_and_abstention_policy",lang_policy)]:
        answered=[i for i,v in enumerate(pred) if v not in {"uncertain","mixed"}]
        languages[name]={**classification(lang_gold,pred),"coverage":ratio(len(answered),len(dev)),
                         "accuracyOnAnswered":ratio(sum(pred[i]==lang_gold[i] for i in answered),len(answered))}
    vocab=build_status_vocabulary({r["utterance_id"] for r in train})
    totals={"span":[0,0,0],"slot":[0,0,0]}; records=[]
    for i,r in enumerate(dev):
        found=[normalize(e) for e in extract(r["text"],status_values=vocab)]
        annotated=json.loads(r["entity_annotations_json"] or "[]")
        gs={(e["slot_name"],e["start"],e["end"]) for e in annotated}
        ps={(e["type"],e["start"],e["end"]) for e in found}
        for key,a,b in [("span",gs,ps),("slot",{e[0] for e in gs},{e[0] for e in ps})]:
            for j,value in enumerate((len(a&b),len(b-a),len(a-b))): totals[key][j]+=value
        records.append({"id":r["utterance_id"],"goldIntent":gold[i],"intent":{k:v[i] for k,v in predictions.items()},
                        "goldLanguage":lang_gold[i],"rawLanguage":lang_raw[i],"policyLanguage":lang_policy[i],
                        "entities":found,"goldEntities":annotated})
    write(out/"nlp_predictions.json",records)
    return {"n":len(dev),"trainN":len(train),"testEvaluated":0,"manifestSHA256":sha(manifest),"datasetSHA256":sha(dataset),
            "intent":scores,"intentDelta":paired_delta([a==b for a,b in zip(gold,predictions["linear_svc"])],
                                                       [a==b for a,b in zip(gold,predictions["logistic_regression"])]),
            "language":languages,"deterministicEntities":{k:prf(*v) for k,v in totals.items()},
            "limitations":["Development labels pending human review; not independent performance.",
                           "Paired SVC/LR fit identical train rows and character features; production model separately includes ontology examples.",
                           "Language models and thresholds already selected using development data.",
                           "Entity slot metric compares slot presence, not legal correctness; normalization gold unavailable.",
                           "No reviewed SLM comparison set supplied."]}

def probe(out):
    from app.schemas.llm import Explanation
    from app.services.llm.grounding_validator import validate
    # Fictional administrative source cards, not legal records or assertions.
    mutations={
      "negation_reversal":lambda s:s.replace("is open","is not open"),
      "number_swap":lambda s:s.replace("card 12","card 99"),
      "jurisdiction_swap":lambda s:s.replace("Andhra Pradesh","Telangana"),
      "date_version_swap":lambda s:s.replace("2024","2025"),
      "condition_removal":lambda s:s.replace(" if the desk is staffed",""),
      "outcome_flip":lambda s:s.replace("is open","is closed"),
      "cross_document_mismatch":lambda s:"The unrelated blue card describes a library.",
      "unsupported_citation":lambda s:s}
    fixtures=[]; predictions=[]
    for split,desk in [("development","Amber"),("reserved_probe","Cobalt")]:
        clean=f"Fictional {desk} desk in Andhra Pradesh is open under card 12 version 2024 if the desk is staffed."
        package={"evidence":[{"evidenceId":"EVID:card","passage":clean,"provision":"Fictional card"}],
                 "supportedActions":[],"uncertainties":[],"facts":[]}
        for kind,mutate in mutations.items():
            for corrupt in (False,True):
                text=mutate(clean) if corrupt else clean
                ids=["EVID:missing"] if corrupt and kind=="unsupported_citation" else ["EVID:card"]
                output=Explanation(answer=text,explanation=text,legalClaims=[{"text":text,"evidenceIds":ids}],
                                   uncertainties=[],recommendedActions=[],language="english",requiresHumanHelp=False)
                result=validate(output,package)
                row={"id":f"{split}:{kind}:{corrupt}","split":split,"type":kind,"corrupt":corrupt,
                     "source":clean,"hypothesis":text,"evidenceIds":ids,"humanReview":"PENDING"}
                fixtures.append(row)
                predictions.append({**row,"enabledFlag":not result["accepted"],"disabledFlag":False,"reasons":result["reasonCodes"]})
    write(out/"probe_cases.json",fixtures);write(out/"probe_predictions.json",predictions)
    groups={}
    for kind in mutations:
        rows=[r for r in predictions if r["split"]=="reserved_probe" and r["type"]==kind]
        bad=[r for r in rows if r["corrupt"]];clean=[r for r in rows if not r["corrupt"]]
        tp=sum(r["enabledFlag"] for r in bad);fp=sum(r["enabledFlag"] for r in clean)
        groups[kind]={"corruptedN":len(bad),"cleanN":len(clean),"detectionRate":ratio(tp,len(bad)),
                      "falsePositiveRate":ratio(fp,len(clean)),"detection95Wilson":wilson(tp,len(bad)),
                      "disabledDetectionRate":0.0,"disabledFalsePositiveRate":0.0}
    return {"n":16,"developmentN":16,"perType":groups,"threshold":"Fixed production Boolean gate; no numeric threshold fitted.",
            "selection":"Pre-existing validator frozen before constructing the probe; development cases are for harness checks only.",
            "limitations":["Synthetic fictional source cards; all labels PENDING human review.",
                           "Reserved probe is template-related to development; not an independent benchmark or production hallucination rate.",
                           "Clean pairs repeat across types; do not aggregate as independent observations.",
                           "Citation/regex gate is not an entailment model and can miss semantic corruption.",
                           "Disabled comparison is offline accept-all only; production checks unchanged."]}

def run(args):
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id): raise ValueError("Invalid run ID")
    out=ROOT/"phase7"/args.run_id
    out.mkdir(parents=True,exist_ok=False)
    from app.services.research.protocol import snapshot
    snapshot(out,vars(args))
    result={"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),
            "protocol":"phase7-development-v1","split":"development only; no grouped test evaluation",
            "python":platform.python_version(),"sklearn":sklearn.__version__,"seed":471,
            "command":vars(args),"reviewStatus":"PENDING; no human ratings",
            "definitions":{"accuracy":"correct / cases","macroF1":"unweighted mean class F1","precision":"TP/(TP+FP)",
                           "recall":"TP/(TP+FN)","f1":"2TP/(2TP+FP+FN)","coverage":"non-abstained / cases",
                           "detectionRate":"flagged corrupted / corrupted","falsePositiveRate":"flagged clean / clean",
                           "delta":"variant minus baseline; multiply rates by 100 for percentage points"},
            "unavailable":{"slmExtraction":"Requires separately reviewed examples; use phase7_slm_compare.py",
                           "ruleApplicability":"No reviewed applicability gold; historical exposure proxy only",
                           "semanticEntailment":"No configured license-reviewed NLI checkpoint",
                           "humanUsefulness":"No blinded human evaluation",
                           "newRetrieval":"Historical queries already exposed; no independent held-out ranking set",
                           "newAdaptive":"Historical recorded-conversation proxy only"}}
    result["sourceHashes"]={str(p.relative_to(BACKEND_DIR)):sha(p) for folder in ("app","scripts")
                            for p in (BACKEND_DIR/folder).rglob("*.py")}
    result["modelHashes"]={p.name:sha(p) for p in (BACKEND_DIR/"artifacts").glob("*.joblib")}
    try: result["gitRevision"]=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except (OSError,subprocess.SubprocessError): result["gitRevision"]=None
    write(out/"protocol.json",result)
    if args.nlp: result["nlp"]=nlp(out)
    if args.probe: result["faithfulness"]=probe(out)
    write(out/"metrics.json",result)
    print(json.dumps({"run":str(out),"nlpN":result.get("nlp",{}).get("n"),"probeN":result.get("faithfulness",{}).get("n")}))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True);parser.add_argument("--nlp",action="store_true");parser.add_argument("--probe",action="store_true")
    run(parser.parse_args())
