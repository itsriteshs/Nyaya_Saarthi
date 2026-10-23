"""Development-only ranking and recorded-context proxies; no test queries."""
import argparse
import csv
import json
import re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from app.config import BACKEND_DIR,DATASET_DIR
from scripts.phase7_research import sha,write
from scripts.phase6_retrieval_eval import ranked,metrics
from app.services.research.metrics import ratio,paired_delta

def weighted_fusion(lexical,semantic,lexical_weight):
    values=Counter()
    for ranking,weight in ((lexical,lexical_weight),(semantic,1-lexical_weight)):
        for rank,item in enumerate(ranking,1):values[item]+=weight/(60+rank)
    return sorted(values,key=lambda item:(-values[item],item))

def run(args):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",args.run_id): raise ValueError("Invalid run ID")
    out=BACKEND_DIR/"experiments/phase7"/args.run_id;out.mkdir(parents=True,exist_ok=False)
    from app.services.research.protocol import snapshot
    snapshot(out,vars(args))
    from app.services.legal.index import load_index,bm25
    from app.services.nlp.ontology import ontology
    manifest_path=BACKEND_DIR/"experiments/manifests/phase6_grouped_split.csv"
    assignment={r["utterance_id"]:r["split"] for r in csv.DictReader(manifest_path.open(encoding="utf-8"))}
    source=DATASET_DIR/"query_provision_relevance.csv"
    queries=defaultdict(lambda:{"gold":set(),"excludedGold":set()})
    retrieval_error=None
    try:
        index,docs,vectors,model=load_index()
        if vectors is None or model is None: raise RuntimeError("Local hybrid index unavailable; no download permitted")
    except (OSError,RuntimeError,ValueError,ImportError) as exc:
        retrieval_error=type(exc).__name__+": "+str(exc)
        index={"status":"unavailable"};docs=[];vectors=None;model=None
    admitted={d["recordId"] for d in docs}
    for r in csv.DictReader(source.open(encoding="utf-8-sig")):
        if assignment.get(r["query_id"])!="dev":continue
        q=queries[r["query_id"]];q["text"]=r["query_text"]
        if r["relevance_label"]=="1":q["gold" if r["provision_id"] in admitted else "excludedGold"].add(r["provision_id"])
    ids=sorted(queries)
    if not ids:raise ValueError("No manifest-matched development queries")
    embeddings=model.encode([queries[i]["text"] for i in ids],normalize_embeddings=True,show_progress_bar=False) if model else []
    rows=[]
    for qid,emb in zip(ids,embeddings):
        q=queries[qid];lex=ranked(bm25(q["text"],docs),docs);sem=ranked((vectors@emb).tolist(),docs)
        fusion=Counter()
        for ranking in (lex,sem):
            for rank,item in enumerate(ranking,1):fusion[item]+=1/(60+rank)
        hybrid=sorted(fusion,key=lambda item:(-fusion[item],item))
        for variant,ranking in [("bm25",lex),("semantic",sem),("hybrid",hybrid),("hybrid_lexical25",weighted_fusion(lex,sem,.25)),("hybrid_lexical75",weighted_fusion(lex,sem,.75))]:
            rows.append({"queryId":qid,"variant":variant,"gold":sorted(q["gold"]),
                         "excludedGold":sorted(q["excludedGold"]),"ranking":ranking})
    results={v:metrics([r for r in rows if r["variant"]==v]) for v in ("bm25","semantic","hybrid","hybrid_lexical25","hybrid_lexical75")}
    base=[bool(set(r["ranking"][:1])&set(r["gold"])) for r in rows if r["variant"]=="hybrid" and r["gold"]]
    deltas={v:paired_delta(base,[bool(set(r["ranking"][:1])&set(r["gold"])) for r in rows if r["variant"]==v and r["gold"]]) for v in ("bm25","semantic")}
    conv_path=DATASET_DIR/"adaptive_conversations.jsonl"
    records=[]
    for line in conv_path.read_text(encoding="utf-8").splitlines():
        c=json.loads(line)
        if c.get("split") not in {"dev","validation"}:continue
        required={r["slot_name"] for r in ontology()["slots"].get(c["primary_intent_id"],[])
                  if r["required_level"]=="required" and json.loads(r.get("required_when_json") or "{}").get("when")=="intent_context"}
        first=next((t for t in c["turns"] if t.get("speaker")=="user"),{}).get("slot_updates",{})
        final=c.get("final_slot_state",{});seen=set(first);redundant=0;questions=0
        for t in c["turns"]:
            if t.get("speaker")=="system" and t.get("asks_for_slot"):
                questions+=1;redundant+=t["asks_for_slot"] in seen
            seen.update(t.get("slot_updates",{}))
        records.append({"id":c["conversation_id"],"requiredN":len(required),"initial":len(required&first.keys()),
                        "final":len(required&final.keys()),"questions":questions,"redundant":redundant,
                        "complete":bool(required) and required<=final.keys()})
    total=sum(r["requiredN"] for r in records);qn=sum(r["questions"] for r in records)
    adaptive={"n":len(records),"requiredSlotObservations":total,
              "initialCoverage":ratio(sum(r["initial"] for r in records),total),
              "finalCoverage":ratio(sum(r["final"] for r in records),total),
              "redundantQuestionRate":ratio(sum(r["redundant"] for r in records),qn),
              "meanQuestions":ratio(qn,len(records)),
              "completionRate":ratio(sum(r["complete"] for r in records),sum(bool(r["requiredN"]) for r in records))}
    write(out/"retrieval_predictions.json",rows);write(out/"context_predictions.json",records)
    write(out/"metrics.json",{"schemaVersion":1,"runId":args.run_id,"timestamp":datetime.now(timezone.utc).isoformat(),
         "split":"development only","reviewStatus":"PENDING","retrieval":results if model else None,"retrievalUnavailableReason":retrieval_error,"recall1DeltaFromHybrid":deltas if model else None,
         "adaptiveRecordedProxy":adaptive,"adaptiveSourceSplit":"validation (development)","index":index,"manifestSHA256":sha(manifest_path),
         "datasetHashes":{source.name:sha(source),conv_path.name:sha(conv_path)},"command":vars(args),
         "definitions":{"recallAtK":"mean fraction of admitted gold IDs in top k over answerable queries",
                        "MRR":"mean reciprocal first relevant rank over answerable queries",
                        "coverage":"recorded required slots captured / required-slot observations",
                        "completion":"all unconditional required slots present / conversations with requirements"},
         "limitations":["Development relevance labels are pending review and queries were exposed historically.",
                        "Global eligible corpus ranking only, not matter-specific applicability.",
                        "Recall@5 is weak with only four eligible documents; unjudged precision unavailable.",
                        "Adaptive comparison uses recorded slot updates, not current generated conversations.",
                        "Conditional requirements and legal conclusions not scored; no overall score."]})
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);run(p.parse_args())
