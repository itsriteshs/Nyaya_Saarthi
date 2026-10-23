"""Opt-in paired extraction evaluation; requires reviewed development examples."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from app.config import BACKEND_DIR
from app.services.research.metrics import prf, ratio
from scripts.phase7_research import sha, write

def reviewed_cases(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("split")!="development" or data.get("reviewStatus")!="REVIEWED" or not data.get("reviewer"):
        raise ValueError("A named human reviewer and REVIEWED development labels are required")
    cases=data["cases"]
    if not cases or len({c["id"] for c in cases})!=len(cases): raise ValueError("Nonempty unique cases required")
    for c in cases:
        ref=datetime.fromisoformat(c["referenceDatetime"])
        if ref.tzinfo is None: raise ValueError("Timezone-aware referenceDatetime required")
        for e in c["entities"]:
            if c["text"][e["start"]:e["end"]]!=e["quote"]: raise ValueError("Gold quote must match offsets")
            if "normalizedValue" not in e: raise ValueError("Explicit normalization label required")
    return data

def run(args):
    from app.services.nlp.entity_extractor import extract
    from app.services.nlp.normalizer import normalize
    from app.services.nlp.slm_extractor import interpret, IntakeFailure, PROMPT_VERSION
    from app.services.nlp.slot_detector import detect_slots
    from app.services.llm.model_registry import MODELS, settings
    from app.services.llm.local_runtime import OllamaProvider
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id): raise ValueError("Invalid run ID")
    source=Path(args.cases);dataset=reviewed_cases(source)
    out=BACKEND_DIR/"experiments/phase7"/args.run_id;out.mkdir(parents=True,exist_ok=False)
    from app.services.research.protocol import snapshot
    snapshot(out,vars(args))
    os.environ["NYAYA_INTAKE_SLM_ENABLED"]="true";os.environ["NYAYA_INTAKE_MODEL"]=args.model
    write(out/"cases.json",dataset)
    rows=[]
    for c in dataset["cases"]:
        for variant in ("deterministic_no_slm","slm"):
            start=time.perf_counter();error=None;metadata={}
            try:
                ref=datetime.fromisoformat(c["referenceDatetime"])
                if variant=="slm": found,metadata=interpret(c["text"],ref)
                else: found=[normalize(e) for e in extract(c["text"],ref)]
            except IntakeFailure as exc:
                found=[];error=exc.reason;metadata=exc.metadata
            gold={(e["slot"],e["normalizedValue"]) for e in c["entities"]}
            pred={(e["type"],e.get("normalizedValue")) for e in found}
            gs={(e["slot"],e["start"],e["end"]) for e in c["entities"]}
            ps={(e["type"],e["start"],e["end"]) for e in found}
            asked={r["slot"] for r in detect_slots(c["intentId"],found)["missingSlots"]}
            supplied={e["slot"] for e in c["entities"] if e.get("status","resolved")=="resolved"}
            rows.append({"id":c["id"],"variant":variant,"entities":found,"metadata":metadata,"failureReason":error,
                         "latencyMs":round((time.perf_counter()-start)*1000),"slot":prf(len(gold&pred),len(pred-gold),len(gold-pred)),
                         "span":prf(len(gs&ps),len(ps-gs),len(gs-ps)),"redundantMissingSlots":sorted(asked&supplied),
                         "questionCount":len(asked),"exactSpanSet":gs==ps,
                         "alignedNormalizationN":sum((e["type"],e["start"],e["end"]) in gs for e in found),
                         "alignedNormalizationCorrect":sum(any(e["type"]==g["slot"] and e["start"]==g["start"] and e["end"]==g["end"] and e.get("normalizedValue")==g["normalizedValue"] for g in c["entities"]) for e in found),"unresolved":sum(e["status"]!="resolved" for e in found),
                         "normalizationCorrect":sum((e["type"],e.get("normalizedValue")) in gold for e in found),
                         "unsupported":len(pred-gold),"predictedN":len(pred)})
    result={}
    for variant in ("deterministic_no_slm","slm"):
        subset=[r for r in rows if r["variant"]==variant]
        result[variant]={"n":len(subset)}
        for key in ("slot","span"):
            result[variant][key]=prf(*(sum(r[key][k] for r in subset) for k in ("tp","fp","fn")))
        result[variant].update({"failureRate":ratio(sum(bool(r["failureReason"]) for r in subset),len(subset)),
            "exactSpanSetAccuracy":ratio(sum(r["exactSpanSet"] for r in subset),len(subset)),
            "normalizationAccuracyOnAlignedSpans":ratio(sum(r["alignedNormalizationCorrect"] for r in subset),sum(r["alignedNormalizationN"] for r in subset)),
            "fallbackRate":0.0,"fallbackPolicy":"No extraction fallback in SLM-only production",
            "meanLatencyMs":sum(r["latencyMs"] for r in subset)/len(subset),
            "unsupportedExtractionRate":ratio(sum(r["unsupported"] for r in subset),sum(r["predictedN"] for r in subset)),
            "redundantMissingQuestionRate":ratio(sum(len(r["redundantMissingSlots"]) for r in subset),sum(r["questionCount"] for r in subset))})
    write(out/"predictions.json",rows)
    write(out/"metrics.json",{"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),
         "split":"reviewed development","reviewStatus":dataset["reviewStatus"],"reviewer":dataset["reviewer"],
         "datasetSHA256":sha(source),"command":vars(args),"model":vars(MODELS[args.model]),"promptVersion":PROMPT_VERSION,
         "runtime":OllamaProvider(settings()["url"]).availability(),"extraction":result,
         "limitations":["Question rate is a missing-slot proxy with gold intent, not generated full conversations.",
                        "Unsupported means disagreement with exhaustive reviewed labels, not independently proven invention.",
                        "No blinded usefulness or legal correctness evaluation."]})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--cases",required=True)
    p.add_argument("--model",choices=["llama3.2-3b","mistral-7b"],default="llama3.2-3b")
    run(p.parse_args())
