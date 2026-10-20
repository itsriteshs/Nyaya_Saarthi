"""Compare three rankers on the same admitted provision corpus and pending labels."""
import json
from collections import Counter, defaultdict
from app.config import BACKEND_DIR, DATASET_DIR
from app.services.dataset_loader import load_dataset
from app.services.legal.index import bm25, load_index

ROOT = BACKEND_DIR / "experiments"


def ranked(scores, docs):
    return [docs[i]["recordId"] for i in sorted(range(len(docs)), key=lambda i: (-scores[i], docs[i]["recordId"])) if scores[i] > 0]


def metrics(rows):
    count = len(rows)
    result = {"n": count, "answerable": sum(bool(r["gold"]) for r in rows)}
    relevant = [r for r in rows if r["gold"]]
    for k in (1, 3, 5):
        result[f"recall@{k}"] = sum(len(set(r["ranking"][:k]) & set(r["gold"])) / len(r["gold"]) for r in relevant) / len(relevant) if relevant else None
        result[f"hit@{k}"] = sum(bool(set(r["ranking"][:k]) & set(r["gold"])) for r in relevant) / len(relevant) if relevant else None
    result["mrr"] = sum(next((1 / (i + 1) for i, name in enumerate(r["ranking"]) if name in r["gold"]), 0) for r in relevant) / len(relevant) if relevant else None
    result["nonemptyRankingRate"] = sum(bool(r["ranking"]) for r in rows) / count if count else None
    return result


def run():
    manifest, docs, vectors, model = load_index()
    if manifest["retrievalMode"] != "hybrid" or vectors is None or model is None:
        raise RuntimeError("Hybrid local index is required for a three-way comparison")
    _, raw = load_dataset(DATASET_DIR / "query_provision_relevance.csv")
    admitted = {d["recordId"] for d in docs}
    queries = defaultdict(lambda: {"text": "", "positive": set(), "excludedPositive": set(), "judged": set()})
    for _, row in raw:
        if not isinstance(row, dict): continue
        q = queries[row["query_id"]]
        if q["text"] and q["text"] != row["query_text"]:
            raise ValueError("Query ID maps to conflicting texts")
        q["text"] = row["query_text"]
        q["judged"].add(row["provision_id"])
        if row["relevance_label"] == "1":
            (q["positive"] if row["provision_id"] in admitted else q["excludedPositive"]).add(row["provision_id"])
    ids = sorted(queries)
    embeddings = model.encode([queries[q]["text"] for q in ids], batch_size=32,
                              normalize_embeddings=True, show_progress_bar=False)
    outputs = {name: [] for name in ("bm25", "semantic", "hybrid")}
    for qid, embedding in zip(ids, embeddings):
        q = queries[qid]
        lexical = bm25(q["text"], docs)
        semantic = (vectors @ embedding).tolist()
        lr = ranked(lexical, docs)
        sr = ranked(semantic, docs)
        fusion = Counter()
        for ranking in (lr, sr):
            for rank, name in enumerate(ranking, 1): fusion[name] += 1 / (60 + rank)
        hr = sorted(fusion, key=lambda name: (-fusion[name], name))
        for name, ranking in (("bm25", lr), ("semantic", sr), ("hybrid", hr)):
            outputs[name].append({"queryId": qid, "gold": sorted(q["positive"]),
                                  "excludedPositive": sorted(q["excludedPositive"]),
                                  "ranking": ranking, "judgedAdmittedCount": len(q["judged"] & admitted)})
    result = {"label": "exploratory: all relevance judgments are PENDING review",
              "indexVersion": manifest["indexVersion"], "sourceFingerprint": manifest["sourceFingerprint"],
              "corpusSize": len(docs), "queryCount": len(ids),
              "queriesWithExcludedPositive": sum(bool(q["excludedPositive"]) for q in queries.values()),
              "queriesWithNoAdmittedPositive": sum(not q["positive"] for q in queries.values()),
              "variants": {name: metrics(rows) for name, rows in outputs.items()},
              "precisionAtK": None,
              "precisionReason": "Most admitted query-document pairs are unjudged; treating them as negatives would fabricate precision.",
              "protocol": "Rank the same four globally eligible provisions for every query without matter-specific jurisdiction, date, or domain filters; this measures ranking only. Queries without an admitted positive are reported separately.",
              "limitations": ["Synthetic relevance pairs are not human reviewed.",
                              "The eligible corpus contains only four provisions; Recall@5 has little discrimination.",
                              "This is not an end-to-end legal applicability score."]}
    path = ROOT / "metrics" / "phase6_retrieval.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    pred = ROOT / "predictions" / "phase6_retrieval.jsonl"
    pred.parent.mkdir(parents=True, exist_ok=True)
    pred.write_text("".join(json.dumps({"variant": name, **row}) + "\n" for name, rows in outputs.items() for row in rows), encoding="utf-8")
    return {"corpusSize": len(docs), "queryCount": len(ids), "answerable": result["variants"]["bm25"]["answerable"],
            "excludedPositiveQueries": result["queriesWithExcludedPositive"],
            "variants": {name: {k: value for k, value in score.items() if k in ("recall@1", "recall@3", "recall@5", "mrr")} for name, score in result["variants"].items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
