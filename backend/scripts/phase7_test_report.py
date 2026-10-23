"""Import JUnit assertions, never invent a live model or human judge score."""
import argparse,json
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from app.config import BACKEND_DIR
from scripts.phase7_research import write

def run(source,out):
    tree=ET.parse(source);cases=tree.findall(".//testcase")
    rows=[{"name":c.attrib["name"],"module":c.attrib.get("classname"),"seconds":float(c.attrib.get("time",0)),
           "status":"failed" if c.find("failure") is not None or c.find("error") is not None else "skipped" if c.find("skipped") is not None else "passed"} for c in cases]
    out.mkdir(parents=True,exist_ok=False)
    write(out/"metrics.json",{"schemaVersion":1,"runId":out.name,"timestamp":datetime.now(timezone.utc).isoformat(),"split":"automated component/API fixture tests; not human or model QA evaluation","reviewStatus":"executable assertions",
        "testing":{"n":len(rows),"passed":sum(r["status"]=="passed" for r in rows),"failed":sum(r["status"]=="failed" for r in rows),"cases":rows},"limitations":["Unit/API assertions are not end-to-end real-user acceptance or legal correctness.","No model judge runs in this suite; model integration is separately documented."]})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--run-id",required=True);a=p.parse_args()
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",a.run_id):raise ValueError("Invalid run ID")
    run(a.source,BACKEND_DIR/"experiments/phase7"/a.run_id)
