"""Isolated R0/R1/R2/R3 pilot. Unvalidated outputs never enter citizen guidance."""
import argparse,json,re,time
from copy import deepcopy
from datetime import datetime,timezone
from app.config import BACKEND_DIR
from scripts.phase7_research import write,sha
from app.services.research.protocol import snapshot
from app.services.llm.model_registry import MODELS,settings
from app.services.llm.local_runtime import OllamaProvider,RuntimeFailure
from app.services.llm.response_parser import parse_response
from app.services.llm.grounding_validator import validate
from app.services.llm.output_checks import check_language
from app.services.llm.prompt_builder import messages,response_schema,PROMPT_VERSION

def evidence_condition(original,condition):
    if condition not in {"R0","R1","R2"}:raise ValueError("Unknown condition")
    package=deepcopy(original)
    if condition in {"R0","R1"}:package["ruleEvaluations"]=[];package["supportedActions"]=[]
    if condition=="R0":package["evidence"]=[]
    return package

def run(args):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id):raise ValueError("Invalid run ID")
    out=BACKEND_DIR/"experiments/phase7"/args.run_id;out.mkdir(parents=True,exist_ok=False);snapshot(out,vars(args))
    source=BACKEND_DIR/"experiments/manifests/phase6_evidence_packages.json"
    cases=json.loads(source.read_text(encoding="utf-8"))["cases"][:args.limit]
    config=settings();provider=OllamaProvider(config["url"]);availability=provider.availability();records=[]
    result={"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),"split":"historical frozen synthetic development pilot",
            "reviewStatus":"PENDING","configuration":config,"availability":availability,"sourceSHA256":sha(source),"command":vars(args),"promptVersion":PROMPT_VERSION,
            "unavailable":{"claimSupport":"Expert-reviewed claim/source pairs required","hallucinationRate":"No reviewed rubric labels","incorrectRefusal":"Answerability gold not reviewed"},
            "limitations":["R0/R1 use same structural prompt but differ only in evidence. R2 also supplies rules and enforces rejection.","All generated outputs screened offline for comparison; R0/R1 are NOT approved citizen outputs.","Citation validity and gate pass are structural proxies; no legal correctness measured.","Pilot selection, one English language, one trial; no independent test."]}
    for case in cases:
        records.append({"caseId":case["caseId"],"model":"deterministic","condition":"R3","output":case["baseline"],"provenance":"frozen baseline","latencyMs":None})
        for model_id,spec in MODELS.items():
            for condition in ("R0","R1","R2"):
                package=evidence_condition(case["package"],condition)
                row={"caseId":case["caseId"],"model":model_id,"checkpoint":spec.checkpoint,"condition":condition,"schemaPass":False,
                     "output":None,"gateAccepted":None,"languagePass":None,"failure":None,"fallback":False,"productionEligible":False}
                started=time.perf_counter()
                try:
                    if not availability["models"][model_id]["available"]:raise RuntimeFailure(availability["models"][model_id]["status"])
                    response=provider.generate(spec.runtime_name,messages(package,case["question"],"english"),temperature=0,
                        max_tokens=config["maxTokens"],timeout=config["timeout"],output_schema=response_schema(package,"english"))
                    row.update({"rawOutput":response.text,"promptTokens":response.prompt_tokens,"outputTokens":response.output_tokens})
                    output=parse_response(response.text);row["schemaPass"]=True;row["output"]=output.model_dump()
                    # Same frozen full evidence reference screens every condition, even R0.
                    verdict=validate(output,case["package"]);row["validation"]=verdict;row["gateAccepted"]=verdict["accepted"]
                    try:check_language(output,"english");row["languagePass"]=True
                    except ValueError:row["languagePass"]=False
                    row["fallback"]=condition=="R2" and not(verdict["accepted"] and row["languagePass"])
                except (RuntimeFailure,ValueError) as exc:row["failure"]=str(exc);row["fallback"]=condition=="R2"
                row["latencyMs"]=round((time.perf_counter()-started)*1000);records.append(row)
                write(out/"rag_predictions.json",records);result["rag"]={"n":len(cases),"records":records};write(out/"metrics.json",result)
                print(json.dumps({k:row[k] for k in ("model","condition","failure","gateAccepted")}),flush=True)
    result["rag"]={"n":len(cases),"records":records};write(out/"metrics.json",result)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);p.add_argument("--limit",type=int,choices=range(1,4),default=3);run(p.parse_args())
