"""Score saved development predictions; never reruns intake or reads test rows."""
import argparse,json,re
from collections import defaultdict,Counter
from datetime import datetime,timezone
from scipy.optimize import linear_sum_assignment
import numpy as np
from app.config import BACKEND_DIR
from app.services.research.metrics import prf
from scripts.phase7_research import write,sha

def matched(gold,pred,relaxed=False):
    scores=np.zeros((len(gold),len(pred)))
    for i,g in enumerate(gold):
        for j,p in enumerate(pred):
            if g["slot_name"]!=p["type"]:continue
            intersection=max(0,min(g["end"],p["end"])-max(g["start"],p["start"]))
            union=max(g["end"],p["end"])-min(g["start"],p["start"])
            scores[i,j]=int(intersection/union>=.5) if relaxed and union else int(g["start"]==p["start"] and g["end"]==p["end"])
    if not scores.size:return 0
    a,b=linear_sum_assignment(-scores)
    return int(scores[a,b].sum())
def run(args):
    for value in (args.run_id,args.source_run):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",value):raise ValueError("Invalid run")
    base=BACKEND_DIR/"experiments/phase7";source=base/args.source_run/"nlp_predictions.json"
    rows=json.loads(source.read_text(encoding="utf-8"));counts=defaultdict(Counter);types=defaultdict(Counter)
    for r in rows:
        gold=r["goldEntities"];pred=r["entities"]
        for kind in ("exact","relaxed"):
            tp=matched(gold,pred,kind=="relaxed");counts[kind].update(tp=tp,fp=len(pred)-tp,fn=len(gold)-tp)
        for slot in {g["slot_name"] for g in gold}|{p["type"] for p in pred}:
            gs=[g for g in gold if g["slot_name"]==slot];ps=[p for p in pred if p["type"]==slot];tp=matched(gs,ps)
            types[slot].update(tp=tp,fp=len(ps)-tp,fn=len(gs)-tp)
    out=base/args.run_id;out.mkdir(exist_ok=False)
    write(out/"metrics.json",{"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),"split":"saved development predictions only","reviewStatus":"PENDING",
        "entities":{"n":len(rows),"scores":{k:prf(v["tp"],v["fp"],v["fn"]) for k,v in counts.items()},"byType":{k:prf(v["tp"],v["fp"],v["fn"]) for k,v in types.items()}},"sourceSHA256":sha(source),"command":vars(args),
        "limitations":["Deterministic offline baseline, not production SLM quality.","Relaxed requires same slot and span intersection-over-union >=0.5 with one-to-one maximum matching; threshold fixed before scoring.","Normalized-value gold and verified-fact preservation evaluation unavailable."]})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--source-run",required=True);run(p.parse_args())
