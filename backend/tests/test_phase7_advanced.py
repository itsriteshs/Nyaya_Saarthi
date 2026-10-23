import numpy as np
import pytest
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from app.services.research.lime import explain

def test_lime_repeatable_and_reports_real_holdout():
    model=Pipeline([("v",TfidfVectorizer()),("c",LinearSVC(random_state=4))]).fit(["red road","red car","blue sky","blue cloud"],["road","road","sky","sky"])
    a=explain(model,"red car on road",300,471);b=explain(model,"red car on road",300,471)
    assert a["tokens"]==b["tokens"]
    assert a["heldOutPerturbations"]==100
    assert 0<=a["heldOutAgreement"]<=1
    assert np.isfinite(a["heldOutR2"])
    assert explain(model,"red")["status"]=="abstained"

def test_examples_are_sanitized_and_exports_bounded(client,tmp_path,monkeypatch):
    import json
    monkeypatch.setattr("app.api.research.ROOT",tmp_path)
    root=tmp_path/"phase7"/"fixture";root.mkdir(parents=True)
    (root/"metrics.json").write_text(json.dumps({"nlp":{"n":1}}))
    (root/"nlp_predictions.json").write_text(json.dumps([{"id":"synthetic","goldIntent":"I","intent":{"svc":"I"},"private":"SECRET"}]))
    result=client.get("/api/v1/research/runs/fixture/examples")
    assert result.status_code==200 and "SECRET" not in result.text
    assert client.get("/api/v1/research/runs/fixture/exports").json()=={"files":[]}
    assert client.get("/api/v1/research/runs/fixture/exports/missing.png").status_code==404
    assert client.get("/api/v1/research/runs/bad.id/examples").status_code==422


def test_rag_treatments_are_controlled_and_do_not_mutate_original():
    from scripts.phase7_rag import evidence_condition
    original={"evidence":[{"evidenceId":"E1"}],"ruleEvaluations":[{"id":"rule"}],"supportedActions":[],"facts":[{"value":"reported"}]}
    assert not evidence_condition(original,"R0")["evidence"]
    assert evidence_condition(original,"R1")["evidence"]==original["evidence"]
    assert not evidence_condition(original,"R1")["ruleEvaluations"]
    assert evidence_condition(original,"R2")==original
    assert len(original["ruleEvaluations"])==1
    with pytest.raises(ValueError):evidence_condition(original,"invalid")

def test_publication_export_uses_values_and_refuses_overwrite(tmp_path):
    import json
    from scripts.phase7_export import export
    (tmp_path/"metrics.json").write_text(json.dumps({"runId":"test-fixture-only","retrieval":{"fixture":{"n":1,"recall@1":.5,"recall@3":.5,"mrr":.5}}}))
    figures=export(tmp_path)
    assert len(figures)==3
    assert (tmp_path/"publication/RET_mrr.png").read_bytes().startswith(b"\x89PNG")
    assert "<svg" in (tmp_path/"publication/RET_mrr.svg").read_text()
    assert "0.5" in (tmp_path/"publication/TABLE_VII_retrieval.csv").read_text(encoding="utf-8-sig")
    with pytest.raises(FileExistsError):export(tmp_path)


def test_fusion_sensitivity_changes_only_ranking():
    from scripts.phase7_retrieval_context import weighted_fusion
    lexical=["a","b"];semantic=["b","a"]
    assert weighted_fusion(lexical,semantic,.75)[0]=="a"
    assert weighted_fusion(lexical,semantic,.25)[0]=="b"
    assert lexical==["a","b"] and semantic==["b","a"]


def test_relaxed_spans_cannot_double_count():
    from scripts.phase7_entity_diagnostic import matched
    gold=[{"slot_name":"SPEED","start":0,"end":4}]
    pred=[{"type":"SPEED","start":0,"end":3},{"type":"SPEED","start":0,"end":4}]
    assert matched(gold,pred,True)==1
    assert matched(gold,[{"type":"STATE","start":0,"end":4}],True)==0
