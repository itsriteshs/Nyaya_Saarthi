"""Publication exports from stored metrics; never performs inference."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from app.config import BACKEND_DIR

def export(path):
    data=json.loads((path/"metrics.json").read_text(encoding="utf-8"))
    out=path/"publication";out.mkdir(exist_ok=False)
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"svg.fonttype":"none"})
    inventory=[]
    def save(fig,name,caption):
        fig.tight_layout()
        for ext in ("png","svg","pdf"):fig.savefig(out/(name+"."+ext),dpi=300,bbox_inches="tight")
        plt.close(fig);inventory.append({"figure":name,"caption":caption,"source":str(path/"metrics.json")})
    def bars(name,values,caption,ylabel="Count"):
        values={k:v for k,v in values.items() if isinstance(v,(int,float))}
        if not values:return
        fig,ax=plt.subplots(figsize=(7.1,max(2.8,.17*len(values))))
        ax.barh(list(values),list(values.values()),color="#17385c");ax.set_xlabel(ylabel);ax.set_title(name.replace("_"," "));save(fig,name,caption)
    def table(name,rows):
        if not rows:return
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with (out/(name+".csv")).open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    if "dataset" in data and "files" in data["dataset"]:
        d=data["dataset"];table("TABLE_I_inventory",[{k:r[k] for k in ("file","n","columnN","sha256")} for r in d["files"]])
        for name,key in (("DATA_language","languages"),("DATA_intent","intents"),("DATA_entities","entityTypes"),("DATA_partitions","partitions")):
            bars(name,d[key],f"Aggregate synthetic corpus audit; N={d['utterances']}; annotation review pending.")
        bars("DATA_records",{r["file"]:r["n"] for r in d["files"]},"Source file record counts; see TABLE I for file hashes.")
        fig,ax=plt.subplots(figsize=(3.5,2.6));ax.hist(d["tokenLengths"],bins=20,color="#17385c");ax.set(xlabel="Whitespace tokens",ylabel="Narratives");save(fig,"DATA_lengths",f"Whitespace length distribution, N={d['utterances']}.")
        fig,ax=plt.subplots(figsize=(7.1,5));m=np.array([[np.mean(list(r["missingPercent"].values()))] for r in d["files"]]);im=ax.imshow(m,aspect="auto",vmin=0,vmax=100);ax.set_yticks(range(len(d["files"])),[r["file"] for r in d["files"]]);ax.set_xticks([0],["Mean missing fields (%)"]);fig.colorbar(im,ax=ax);save(fig,"DATA_missing","Mean missing-field percentages by source file; full field counts in metrics JSON.")
    if "nlp" in data:
        n=data["nlp"];rows=[{"model":k,**{m:v.get(m) for m in ("n","accuracy","macroF1","macroPrecision","macroRecall","weightedF1","trainingMs","meanInferenceMs","p95InferenceMs","artifactBytes")}} for k,v in n["intent"].items()];table("TABLE_III_intent",rows)
        for name,metric in (("INT_01_accuracy","accuracy"),("INT_04_training","trainingMs"),("INT_05_latency","meanInferenceMs")):
            bars(name,{k:v.get(metric) for k,v in n["intent"].items()},f"Same {n['n']} development cases; unreviewed labels; metric={metric}.",metric)
        for model,v in n["intent"].items():
            fig,ax=plt.subplots(figsize=(7.1,6));im=ax.imshow(v["confusionMatrix"],cmap="Blues");ax.set(xlabel="Predicted class index",ylabel="Reference class index",title=model);fig.colorbar(im,ax=ax);save(fig,"INT_02_"+model,f"Confusion matrix N={n['n']}; class order in metrics JSON; development only.")
        bars("NLP_language_intent",{k:v["intentAccuracy"] for k,v in n.get("byLanguage",{}).items()},"Intent accuracy by annotated language; denominators in metrics JSON.","Accuracy")
        table("TABLE_IV_multilingual",[{"language":k,"n":v["n"],"intentAccuracy":v["intentAccuracy"],"spanF1":v["span"]["f1"],"missingF1":v["missingSlots"]["f1"]} for k,v in n.get("byLanguage",{}).items()])
    if "retrieval" in data and data["retrieval"]:
        rows=[{"ranker":k,**v} for k,v in data["retrieval"].items()];table("TABLE_VII_retrieval",rows)
        for metric in ("recall@1","recall@3","mrr"):bars("RET_"+metric.replace("@","at"),{k:v[metric] for k,v in data["retrieval"].items()},"Identical development queries and eligible corpus; label review pending.",metric)
    if "adaptiveRecordedProxy" in data:
        a=data["adaptiveRecordedProxy"];table("TABLE_VI_adaptive",[a]);bars("CONV_coverage",{k:a[k] for k in ("initialCoverage","finalCoverage")},f"Recorded development-data proxy, N={a['n']}; not generated app comparison.","Coverage")
    if "generation" in data:
        table("TABLE_VIII_generation",[{"model":k,"n":v["n"],"acceptance":v["acceptanceRate"],"fallback":v["fallbackRate"],"latencyMs":v["meanLatencyMs"]} for k,v in data["generation"].items()]);bars("LLM_acceptance",{k:v["acceptanceRate"] for k,v in data["generation"].items()},"Three English synthetic development packages per model; structural proxy only.","Acceptance rate")
    if "lime" in data and "cases" in data["lime"]:
        l=data["lime"];table("TABLE_XI_xai",[{"case":c["id"],"stability300":c["top5Stability300"],"meanHeldOutR2":float(np.mean([r["heldOutR2"] for r in c["runs"]]))} for c in l["cases"]]);bars("XAI_02_fidelity",{c["id"]:float(np.mean([r["heldOutR2"] for r in c["runs"]])) for c in l["cases"]},f"LIME-style weighted Ridge; {l['n']} selected synthetic development cases.","Held-out R²")
        bars("XAI_03_stability",{c["id"]:c["top5Stability300"] for c in l["cases"]},"Top-five position Jaccard over three seeds, 300 perturbations.","Jaccard")
        for c in l["cases"][:1]:bars("XAI_01_tokens",{str(t["position"])+":"+t["token"]:t["weight"] for t in c["runs"][0]["tokens"][:12]},"Token contributions to SVM margin surrogate; not probabilities or legal evidence.","Coefficient")
    if "rag" in data:
        records=data["rag"]["records"];rows=[]
        for model in ("llama3.2-3b","mistral-7b"):
            for condition in ("R0","R1","R2"):
                rs=[r for r in records if r.get("model")==model and r.get("condition")==condition]
                if rs: rows.append({"model":model,"condition":condition,"n":len(rs),"schemaPassRate":sum(r["schemaPass"] for r in rs)/len(rs),"failureRate":sum(bool(r["failure"]) for r in rs)/len(rs),"semanticClaimSupport":"Not measured; reviewed labels required"})
        table("TABLE_IX_rag_proxies",rows)
        bars("RAG_schema",{r["model"]+" "+r["condition"]:r["schemaPassRate"] for r in rows},"One frozen English development case per model/condition. Schema proxy, not legal support.","Schema pass / attempted")
    table("figure_inventory",inventory)
    (out/"report.md").write_text("# Publication evidence\n\nRun: "+data["runId"]+"\n\nStatus: development diagnostics, pending human review. No independent legal accuracy measured.\n\n"+"\n\n".join(r["figure"]+": "+r["caption"] for r in inventory)+"\n\nUnmeasured tables (including legal claim support and blinded usefulness) must remain Not measured; see source metrics limitations.",encoding="utf-8")
    return inventory
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",a.run_id):raise ValueError("Invalid run ID")
    print(json.dumps(export(BACKEND_DIR/"experiments/phase7"/a.run_id)))
