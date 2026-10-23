"""Opt-in model comparison on identical historical frozen development evidence."""
import argparse
import json
import re
import time
from collections import Counter
from datetime import datetime, timezone
from app.config import BACKEND_DIR
from app.services.llm.model_registry import MODELS, settings
from app.services.llm.local_runtime import OllamaProvider, RuntimeFailure
from app.services.llm.prompt_builder import messages, response_schema, PROMPT_VERSION
from app.services.llm.response_parser import parse_response
from app.services.llm.output_checks import check_language
from app.services.llm.grounding_validator import validate
from app.services.research.metrics import ratio
from scripts.phase7_research import write,sha

def run(args):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id):raise ValueError("Invalid run ID")
    out=BACKEND_DIR/"experiments/phase7"/args.run_id;out.mkdir(parents=True,exist_ok=False)
    from app.services.research.protocol import snapshot
    snapshot(out,vars(args))
    path=BACKEND_DIR/"experiments/manifests/phase6_evidence_packages.json"
    frozen=json.loads(path.read_text(encoding="utf-8"));write(out/"frozen_evidence.json",frozen)
    config=settings();provider=OllamaProvider(config["url"]);available=provider.availability()
    records=[]
    for case in frozen["cases"]:
        for language in args.languages:
            for model_id in ("deterministic","llama3.2-3b","mistral-7b"):
                row={"caseId":case["caseId"],"model":model_id,"language":language,"schemaPass":None,
                     "groundingPass":None,"languagePass":None,"fallback":False,"reasonCodes":[],
                     "evidenceFingerprint":case["package"]["fingerprint"]}
                start=time.perf_counter()
                if model_id=="deterministic":
                    from app.schemas.matter import Guidance
                    baseline=Guidance.model_validate(case["baseline"])
                    ids={e["evidenceId"] for e in case["package"]["evidence"]}
                    row.update({"status":"recorded_baseline","schemaPass":True,"schemaContract":"Guidance, not Explanation",
                                "languagePass":language=="english","outputLanguage":"english",
                                "citationValidityProxy":all(s.evidenceId in ids for s in baseline.sources),
                                "recordedOutput":baseline.model_dump(),"latencyMs":None})
                    if language!="english":row["reasonCodes"]=["DETERMINISTIC_ENGLISH_ONLY"]
                elif not case["package"]["evidence"]:
                    row.update({"status":"skipped","fallback":True,"reasonCodes":["INSUFFICIENT_ELIGIBLE_EVIDENCE"]})
                elif not available["models"][model_id]["available"]:
                    row.update({"status":"runtime_failure","fallback":True,"reasonCodes":[available["models"][model_id]["status"]]})
                else:
                    try:
                        result=provider.generate(MODELS[model_id].runtime_name,messages(case["package"],case["question"],language),
                            temperature=0,max_tokens=config["maxTokens"],timeout=config["timeout"],
                            output_schema=response_schema(case["package"],language))
                        row.update({"rawOutput":result.text,"promptTokens":result.prompt_tokens,"outputTokens":result.output_tokens})
                        try: output=parse_response(result.text);row["schemaPass"]=True
                        except ValueError:row["schemaPass"]=False;raise
                        verdict=validate(output,case["package"]);row["groundingPass"]=verdict["accepted"]
                        row["reasonCodes"]+=verdict["reasonCodes"]
                        row["citationValidityProxy"]=not verdict["unsupportedCitations"]
                        try: check_language(output,language);row["languagePass"]=True
                        except ValueError as exc:row["languagePass"]=False;row["reasonCodes"].append(str(exc))
                        row["fallback"]=not(row["groundingPass"] and row["languagePass"])
                        row["status"]="rejected" if row["fallback"] else "accepted"
                    except (RuntimeFailure,ValueError) as exc:
                        row.update({"fallback":True,"status":"failed"});row["reasonCodes"].append(str(exc))
                if model_id!="deterministic": row["latencyMs"]=round((time.perf_counter()-start)*1000)
                records.append(row)
                write(out/"predictions.json",records)
                print(json.dumps({k:row[k] for k in ("caseId","model","language","status")}),flush=True)
    metrics={}
    for model in ("deterministic",*MODELS):
        rows=[r for r in records if r["model"]==model];usable=[r for r in rows if r["status"]!="unavailable"]
        metrics[model]={"n":len(rows),"evaluatedN":len(usable),"reasonCodes":dict(Counter(c for r in rows for c in r["reasonCodes"]))}
        for field in ("schemaPass","groundingPass","languagePass","citationValidityProxy"):
            observed=[r[field] for r in usable if r.get(field) is not None]
            metrics[model][field]={"rate":ratio(sum(observed),len(observed)),"denominator":len(observed)}
        metrics[model]["acceptanceRate"]=None if model=="deterministic" else ratio(sum(r["status"]=="accepted" for r in usable),len(usable))
        metrics[model]["fallbackRate"]=ratio(sum(r["fallback"] for r in usable),len(usable))
        metrics[model]["meanLatencyMs"]=ratio(sum(r["latencyMs"] for r in usable if r.get("latencyMs") is not None),sum(r.get("latencyMs") is not None for r in usable))
    write(out/"metrics.json",{"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),
         "split":"historical synthetic evidence reused for development only","reviewStatus":"PENDING",
         "generation":metrics,"models":{k:vars(v) for k,v in MODELS.items()},"availability":available,
         "frozenEvidenceSHA256":sha(path),"promptVersion":PROMPT_VERSION,"settings":config,"seed":471,
         "contextTokens":8192,"temperature":0,"command":vars(args),
         "limitations":["No new held-out evaluation; same evidence per case-language for both models.",
                        "Deterministic baseline is the recorded English Guidance output, with a different schema. LLM grounding acceptance is not applicable; baseline latency unrecorded.",
                        "Citation validity is structural only. No semantic support or blinded human ratings.",
                        "Latency includes cold starts and serial model loading; one trial per cell."]})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    p.add_argument("--languages",nargs="+",choices=["english","hindi","hinglish"],default=["english","hindi","hinglish"])
    run(p.parse_args())
