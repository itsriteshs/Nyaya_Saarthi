import json
import pytest
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from app.services.research.attribution import linear_attribution
from app.services.research.trace import trace
from app.services.research.metrics import prf, wilson, paired_delta
from scripts.phase7_slm_compare import reviewed_cases
from scripts.phase7_research import probe

def test_contributions_reconstruct_real_margin():
    model=Pipeline([("vectorizer",TfidfVectorizer(analyzer="char",ngram_range=(2,3))),
                    ("model",LinearSVC(random_state=471))])
    model.fit(["red road","red lane","blue sky","blue cloud","green field","green grass"],["r","r","b","b","g","g"])
    result=linear_attribution(model,"red road green")
    for row in result["classes"]:
        assert row["intercept"]+row["allFeatureSum"]==pytest.approx(row["score"])
        assert all(f["contribution"]>0 for f in row["positive"])
        assert all(f["contribution"]<0 for f in row["negative"])
    assert result["marginGap"]==pytest.approx(result["classes"][0]["score"]-result["classes"][1]["score"])

def test_binary_attribution():
    model=Pipeline([("v",TfidfVectorizer()),("m",LinearSVC())]).fit(["red road","blue sky"],["r","b"])
    result=linear_attribution(model,"red")
    assert len(result["classes"])==2
    for row in result["classes"]:
        assert row["intercept"]+row["allFeatureSum"]==pytest.approx(row["score"])

def test_empty_trace_no_fabrication():
    result=trace({"id":"x","revision":1,"originalText":"Hello"})
    assert result["intent"] is None and result["claims"] is None
    assert result["question"] is None
    assert result["semanticSupport"]["status"]=="unavailable"

def test_trace_preserves_conflict_and_claim():
    claim={"text":"A recorded claim.","evidenceIds":["EVID:a"]}
    fact={"key":"STATE","value":"X","confirmed":False,"resolutionStatus":"ambiguous"}
    result=trace({"id":"x","revision":2,"originalText":"X","facts":[fact],
                  "guidance":{"metadata":{"structuredOutput":{"legalClaims":[claim]},"failureReason":"UNLINKED_CLAIM"}}})
    assert result["claims"]==[claim] and result["facts"]==[fact]
    assert result["generation"]["failureReason"]=="UNLINKED_CLAIM"

def test_denominators_and_uncertainty():
    assert prf(0,0,0)["f1"] is None
    assert prf(1,1,1)["f1"]==.5
    assert wilson(0,0) is None
    assert wilson(1,1)[0]<1
    assert paired_delta([0,1],[1,1])["absolute"]==.5

def test_probe_includes_clean_and_all_attack_types(tmp_path):
    result=probe(tmp_path)
    assert len(result["perType"])==8
    assert all(r["cleanN"]==1 and r["corruptedN"]==1 for r in result["perType"].values())
    assert result["perType"]["unsupported_citation"]["detectionRate"]==1
    assert result["perType"]["negation_reversal"]["detectionRate"]==0
    assert all(r["falsePositiveRate"]==0 for r in result["perType"].values())
    rows=json.loads((tmp_path/"probe_cases.json").read_text())
    assert {r["split"] for r in rows}=={"development","reserved_probe"}

def test_reviewed_data_gate(tmp_path):
    p=tmp_path/"cases.json"
    p.write_text(json.dumps({"split":"test","reviewStatus":"REVIEWED","reviewer":"Example","cases":[]}))
    with pytest.raises(ValueError):reviewed_cases(p)
    p.write_text(json.dumps({"split":"development","reviewStatus":"PENDING","cases":[]}))
    with pytest.raises(ValueError):reviewed_cases(p)

def test_research_contract_and_missing_matter(client):
    result=client.get("/api/v1/research/catalog")
    assert result.status_code==200
    assert result.json()["historical"]["label"].startswith("Historical Phase 6")
    assert client.get("/api/v1/research/runs/invalid.id").status_code==422
    assert client.get("/api/v1/research/runs/missing-artifact").status_code==404
    assert client.get("/api/v1/research/matters/not-uuid/trace").status_code==422
    matter=client.post("/api/v1/matters",json={"originalText":"Test research","language":"english"}).json()
    result=client.get(f"/api/v1/research/matters/{matter['id']}/trace")
    assert result.status_code==200 and result.json()["language"] is None
    assert result.json()["originalText"]=="Test research"

def test_artifact_absence_and_corruption(client,tmp_path,monkeypatch):
    monkeypatch.setattr("app.api.research.ROOT",tmp_path)
    data=client.get("/api/v1/research/catalog").json()
    assert data["runs"]==[] and data["historical"]["ablations"] is None
    p=tmp_path/"phase7"/"broken";p.mkdir(parents=True)
    (p/"metrics.json").write_text("{")
    assert client.get("/api/v1/research/runs/broken").status_code==404


def test_selected_workflow_keeps_original_prediction():
    original={"id":"INT001","score":.4,"attribution":{"classes":[]}}
    selected={"id":"INT002","score":0}
    result=trace({"id":"x","revision":3,"originalText":"road",
                  "nlpAnalysis":{"intent":selected},
                  "conversation":{"intentConfirmed":True,"originalIntentPrediction":original}})
    assert result["intent"]==original and result["selectedWorkflow"]==selected
