"""Aggregate dataset audit and offline local explanation study; no incident DB reads."""
import argparse,csv,json,re,platform,subprocess
from collections import Counter,defaultdict
from datetime import datetime,timezone
import numpy as np
from app.config import BACKEND_DIR,DATASET_DIR
from scripts.phase7_research import write,sha
from app.services.research.protocol import snapshot

def audit(out):
    from app.services.nlp.preprocessing import normalize_text,text_template
    files=[];failures=[]
    for p in sorted(DATASET_DIR.iterdir()):
        if p.suffix not in {".csv",".jsonl"}:continue
        try:
            rows=list(csv.DictReader(p.open(encoding="utf-8-sig"))) if p.suffix==".csv" else [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
            columns=sorted({k for r in rows for k in r if k is not None})
            missing={c:sum(r.get(c) in (None,"") for r in rows) for c in columns}
            files.append({"file":p.name,"n":len(rows),"columnN":len(columns),"missing":missing,
                          "missingPercent":{c:100*v/len(rows) if rows else None for c,v in missing.items()},"sha256":sha(p)})
        except (ValueError,csv.Error) as exc:failures.append({"dataset":p.name,"rowId":None,"field":None,"severity":"error","explanation":str(exc)})
    rows=list(csv.DictReader((DATASET_DIR/"annotated_utterances.csv").open(encoding="utf-8-sig")))
    lengths=[len(r["text"].split()) for r in rows];entities=Counter();invalid=0
    normalized=Counter();templates=defaultdict(set);exact=defaultdict(set)
    for r in rows:
        normalized[normalize_text(r["text"])]+=1;exact[normalize_text(r["text"])].add(r["split"]);templates[text_template(r["text"])].add(r["split"])
        for e in json.loads(r["entity_annotations_json"] or "[]"):
            entities[e["slot_name"]]+=1
            if r["text"][e["start"]:e["end"]]!=e["value"]:invalid+=1
    manifest=BACKEND_DIR/"experiments/manifests/phase6_grouped_split.csv"
    assignments=list(csv.DictReader(manifest.open(encoding="utf-8")));groups=defaultdict(set)
    for r in assignments:
        if r["split"] in {"train","dev","test"}:groups[r["group_id"]].add(r["split"])
    # Existing validator is read-only and reports reference integrity under its declared schema.
    from app.services.legal.guidance import readiness
    from app.services.dataset_validator import audit_dataset
    historical=audit_dataset(DATASET_DIR)
    write(out/"integrity_reference.json",historical)
    result={"sourceFileN":len(files),"files":files,"utterances":len(rows),"uniqueNormalized":len(normalized),
            "languages":dict(Counter(r["language"] for r in rows)),"intents":dict(Counter(r["primary_intent_id"] for r in rows)),
            "entityTypes":dict(entities),"tokenLengths":lengths,"tokenSummary":{"mean":float(np.mean(lengths)),"median":float(np.median(lengths)),"min":min(lengths),"max":max(lengths)},
            "duplicateExtraRows":sum(v-1 for v in normalized.values()),"templateCrossOriginalSplits":sum(len(v)>1 for v in templates.values()),
            "exactCrossOriginalSplits":sum(len(v)>1 for v in exact.values()),"groupCrossDerivedSplits":sum(len(v)>1 for v in groups.values()),
            "partitions":dict(Counter(r["split"] for r in assignments)),"invalidAnnotationSpans":invalid,
            "eligibility":readiness(),"failedChecks":failures,"referenceIntegrity":"Fresh read-only validator output in integrity_reference.json; reference integrity does not establish legal validity",
            "limitations":["Synthetic annotations pending review; no inter-annotator agreement available.","Near-duplicate indicator is digit-masked template equivalence, not semantic duplicate proof.","Token counts are whitespace tokens, not model tokenizer counts."]}
    return result

def lime_study(out):
    from app.services.nlp.intent_classifier import load_intent_model
    from app.services.research.lime import explain
    from app.services.nlp.preprocessing import normalize_text
    model,meta=load_intent_model()
    assignment={r["utterance_id"]:r["split"] for r in csv.DictReader((BACKEND_DIR/"experiments/manifests/phase6_grouped_split.csv").open(encoding="utf-8"))}
    rows=[r for r in csv.DictReader((DATASET_DIR/"annotated_utterances.csv").open(encoding="utf-8-sig")) if assignment.get(r["utterance_id"])=="dev"]
    selected=[]
    for language in sorted({r["language"] for r in rows}):selected.extend([r for r in rows if r["language"]==language][:2])
    records=[]
    for r in selected:
        runs=[explain(model,normalize_text(r["text"]),n,seed) for n in (300,600) for seed in (471,472,473)]
        sets=[{v["position"] for v in a["tokens"][:5]} for a in runs if a["perturbations"]==300]
        jaccards=[len(a&b)/len(a|b) for i,a in enumerate(sets) for b in sets[i+1:]]
        records.append({"id":r["utterance_id"],"input":r["text"],"trueIntent":r["primary_intent_id"],"language":r["language"],
                        "runs":runs,"top5Stability300":float(np.mean(jaccards))})
    write(out/"lime_predictions.json",records)
    return {"n":len(records),"modelVersion":meta["model_version"],"cases":records,
            "meanHeldOutR2":float(np.mean([v["heldOutR2"] for r in records for v in r["runs"]])),
            "meanStability300":float(np.mean([r["top5Stability300"] for r in records])),
            "limitations":["Selected development synthetic examples; not a representative sample.","LIME-style transparent implementation, not the third-party lime package.","Surrogate agreement does not verify the predicted intent or legal facts."]}

def run(args):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id):raise ValueError("Invalid run ID")
    out=BACKEND_DIR/"experiments/phase7"/args.run_id;out.mkdir(parents=True,exist_ok=False);snapshot(out,vars(args))
    result={"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),"split":"development explanation study; aggregate dataset inventory only",
            "reviewStatus":"PENDING","seed":471,"hardware":{"platform":platform.platform(),"processor":platform.processor()},"command":vars(args)}
    for name,enabled,func in (("dataset",args.audit,audit),("lime",args.lime,lime_study)):
        if enabled:
            try:result[name]=func(out)
            except Exception as exc:result[name]={"status":"FAILED","reason":type(exc).__name__+": "+str(exc)}
        write(out/"metrics.json",result)
    print(json.dumps({"run":str(out),"components":list(result)}))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--audit",action="store_true");p.add_argument("--lime",action="store_true");run(p.parse_args())
