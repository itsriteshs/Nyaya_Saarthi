"""Independent offline jobs; preserve successes when another job fails."""
import argparse,json,subprocess,sys
from datetime import datetime,timezone
from app.config import BACKEND_DIR

def main():
    p=argparse.ArgumentParser();p.add_argument("--prefix",required=True);p.add_argument("--local-models",action="store_true");a=p.parse_args()
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}",a.prefix):raise ValueError("Invalid prefix")
    jobs=[("phase7_research",["--nlp","--probe"]),("phase7_advanced",["--audit","--lime"]),("phase7_retrieval_context",[])]
    if a.local_models:jobs.extend([("phase7_generation",[]),("phase7_rag",["--limit","3"])])
    output=BACKEND_DIR/"experiments/phase7"/(a.prefix+"-suite.json")
    if output.exists():raise FileExistsError(output)
    statuses=[]
    for module,flags in jobs:
        command=[sys.executable,"-m","scripts."+module,"--run-id",a.prefix+"-"+module,*flags]
        done=subprocess.run(command,check=False)
        statuses.append({"command":command,"returnCode":done.returncode,"status":"completed" if done.returncode==0 else "failed"})
        output.write_text(json.dumps({"timestamp":datetime.now(timezone.utc).isoformat(),"jobs":statuses},indent=2),encoding="utf-8")
if __name__=="__main__":main()
