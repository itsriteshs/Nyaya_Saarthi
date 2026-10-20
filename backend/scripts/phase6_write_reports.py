"""Render concise Phase 6 research reports from recorded JSON metrics."""
import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
METRICS = BACKEND / "experiments" / "metrics"
REPORTS = BACKEND / "reports"


def load(name):
    return json.loads((METRICS / name).read_text(encoding="utf-8"))


def write(name, body):
    (REPORTS / name).write_text(body.strip() + "\n", encoding="utf-8")


def pct(value):
    return f"{value * 100:.1f}%" if value is not None else "N/A"


def run():
    data = load("phase6_data_audit.json")
    nlp = load("phase6_nlp.json")
    retrieval = load("phase6_retrieval.json")
    ablation = load("phase6_ablations.json")
    llms = {key: load(f"phase6_llm_{key}.json") for key in ("llama3.2-3b", "mistral-7b")
            if (METRICS / f"phase6_llm_{key}.json").exists()}

    write("nlp_results.md", f"""
# Phase 6 NLP results

The source annotation set has {data['sourceRows']:,} utterances (original train/dev/test: 8,000/1,000/1,000). Original splits share {data['exactTextCrossSourceSplits']} normalized texts and {data['digitMaskedTemplateCrossSourceSplits']} digit-masked template families. The derived connected scenario/template manifest has train/dev/test **{nlp['counts']['train']:,}/{nlp['counts']['dev']:,}/{nlp['counts']['test']:,}** and excludes {data['goldTemplateOverlapExcludedRows']:,} rows overlapping gold templates; zero connected groups cross derived partitions. The original test was exposed in prior development, and all labels are pending review. These are exploratory scores, not an independent benchmark.

| Task | Grouped test result | Notes |
|---|---:|---|
| Intent accuracy / macro F1 | {pct(nlp['intent']['accuracy'])} / {pct(nlp['intent']['macroF1'])} | Character SVM chosen on development; word logistic regression also scored 100% on development. Template cues make this an optimistic result. |
| Language coverage / accuracy on answered / overall accuracy | {pct(nlp['language']['coverage'])} / {pct(nlp['language']['accuracyAnswered'])} / {pct(nlp['language']['overallAccuracy'])} | Abstentions count as wrong overall. |
| Prior mixed-script policy overall, same grouped split | {pct(nlp['language']['legacyPolicyOnSameSplit']['overallAccuracy'])} | Phase 6 Devanagari-dominance policy replaces treating any mixed script as `mixed`. |
| Entity exact-span precision / recall / F1 | {pct(nlp['entityExactSpan']['precision'])} / {pct(nlp['entityExactSpan']['recall'])} / {pct(nlp['entityExactSpan']['f1'])} | TP {nlp['entityExactSpan']['tp']}, FP {nlp['entityExactSpan']['fp']}, FN {nlp['entityExactSpan']['fn']}; original offsets. |
| Missing-slot precision / recall / F1 | {pct(nlp['missingSlots']['precision'])} / {pct(nlp['missingSlots']['recall'])} / {pct(nlp['missingSlots']['f1'])} | TP {nlp['missingSlots']['tp']}, FP {nlp['missingSlots']['fp']}, FN {nlp['missingSlots']['fn']}. |
| Missing-slot exact set | {pct(nlp['missingSlots']['exactSetAccuracy'])} | Oracle intent gives the same F1; intent errors are not the driver on this split. |

The main unresolved defect is missing-slot precision: many policy-required `USER_ROLE` and `VEHICLE_CLASS` slots are absent from recorded missing-slot labels. We retained the requirements and report the mismatch. A training-fold-only status phrase vocabulary prevents annotation values in test from entering entity inference. Full per-intent, per-language, per-entity and confusion matrices are in `experiments/metrics/phase6_nlp.json`; case-level predictions are in `experiments/predictions/phase6_nlp.jsonl`. Figures: `experiments/plots/language_policy.png` and `language_confusion.png`.
""")

    rows = "\n".join(f"| {name} | {pct(item['recall@1'])} | {pct(item['recall@3'])} | {pct(item['recall@5'])} | {item['mrr']:.3f} |" for name, item in
                     ((label, retrieval['variants'][key]) for label, key in (("BM25", "bm25"), ("Semantic", "semantic"), ("Hybrid RRF", "hybrid"))))
    write("retrieval_results.md", f"""
# Phase 6 retrieval results

The hybrid index version is `{retrieval['indexVersion']}`; source fingerprint `{retrieval['sourceFingerprint']}`. An isolated offline rebuild using the saved local embedding checkpoint reproduced the same index version, 4 documents and model revision. The admitted corpus contains only {retrieval['corpusSize']} provisions. We ranked the same corpus for {retrieval['queryCount']:,} distinct queries; {retrieval['variants']['hybrid']['answerable']:,} had an admitted positive and {retrieval['queriesWithExcludedPositive']:,} had only an excluded positive. No query-specific jurisdiction, date, or domain filter was applied in this ranking experiment. Production retrieval still applies eligibility, jurisdiction and date filters.

| Ranker | Recall@1 | Recall@3 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
{rows}

Hybrid improves Recall@1 over BM25 by {100*(retrieval['variants']['hybrid']['recall@1']-retrieval['variants']['bm25']['recall@1']):.1f} percentage points and MRR by {retrieval['variants']['hybrid']['mrr']-retrieval['variants']['bm25']['mrr']:.3f}; semantic is slightly higher at @3. Recall@5 is weakly informative with only four eligible provisions. Precision@k is **N/A** because most admitted query-document pairs are unjudged. All relevance labels are pending human review; this is a ranking result, not a legal applicability or answer-quality score. Per-query rankings are saved in `experiments/predictions/phase6_retrieval.jsonl`; figure: `experiments/plots/retrieval_comparison.png`.
""")

    model_rows = "\n".join(f"| {name} | {d['overall']['n']} | {pct(d['overall']['acceptedRate'])} | {pct(d['overall']['fallbackRate'])} | {d['overall']['latencyMs']['median']/1000:.2f} s | {d['overall']['meanOutputTokens']:.1f} |" for name, d in llms.items())
    model_details = "\n".join(
        f"- **{name}** — Ollama `{d['runtimeTag']}` (Q4_K_M), installed digest `{d['installedDigest']}`. "
        f"English/Hindi/Hinglish structural acceptance: "
        + "/".join(pct(d['byLanguage'][language]['acceptedRate']) for language in ('english', 'hindi', 'hinglish'))
        + f". Rejection reason counts: {d['overall']['reasonCodes']}; unsupported actions omitted: {d['overall']['unsupportedActionOmissionCount']}. "
        + f"Mean latency {d['overall']['latencyMs']['mean']/1000:.2f} s; p95 {d['overall']['latencyMs']['p95']/1000:.2f} s."
        for name, d in llms.items())
    safety_rows = "\n".join(
        f"| {name} | {pct(d['overall']['citationValidityProxyRate'])} | "
        f"{d['overall']['unsupportedActionOmissionCount']} | {d['overall']['statuses'].get('grounding_rejected', 0)} | "
        f"{d['overall']['statuses'].get('language_rejected', 0)} | N/A |"
        for name, d in llms.items())
    if not model_rows:
        model_rows = "| Pending | N/A | N/A | N/A | N/A | N/A |"
    write("llm_comparison.md", f"""
# Phase 6 real local LLM comparison

Both models receive identical frozen synthetic evidence packages, prompts (`phase6-grounded-v2`), English/Hindi/Hinglish requests, temperature 0 and output cap. Ollama applies each checkpoint's own chat template. One trial per case-language cell; no seed is exposed by the adapter. Each model has three cases × three languages. Generation latency is measured separately from offline retrieval. Input packages and raw outputs are in `experiments/manifests/phase6_evidence_packages.json` and `experiments/predictions/`.

| Model | Generations | Structurally accepted | Fallback | Median generation latency | Mean output tokens |
|---|---:|---:|---:|---:|---:|
{model_rows}

{model_details}

| Model | Known citation IDs (proxy) | Unsupported actions omitted | Grounding rejected | Language rejected | Semantic claim support |
|---|---:|---:|---:|---:|---:|
{safety_rows}

Acceptance requires parsed schema, requested language, known evidence IDs, literal claim linkage and absence of prohibited numeric or definite claims. Unsupported model-suggested actions are omitted; deterministic next steps remain authoritative. Citation validity is a **structural proxy**. A valid citation does not prove a semantically supported legal claim. No blinded human legal or multilingual quality ratings took place, so comparative usefulness, factual support and fluency are **N/A**. Each model's metrics file includes language-specific outcomes and reason codes. Figure: `experiments/plots/llm_comparison.png`.
""")

    aq = ablation['adaptiveQuestioning']
    rules = ablation['ruleMatching']
    write("ablation_study.md", f"""
# Phase 6 offline ablations

These component comparisons use different case sets and are **not** a single full-pipeline score. Safety controls remain active in production.

| Component comparison | Sample | Measured outcome |
|---|---:|---|
| Initial utterance vs recorded final conversation | {aq['n']} conversations, {aq['requiredSlotObservations']} required-slot observations | Captured coverage {pct(aq['withoutAdaptiveCapturedRate'])} → {pct(aq['recordedFinalCapturedRate'])}, +{100*aq['absoluteChange']:.1f} points; {aq['recordedQuestionCount']} recorded questions; redundant recorded question rate {pct(aq['recordedRedundantQuestionRate'])}; mean {aq['meanRecordedTurns']:.2f} turns. |
| Current first-question policy vs recorded first question | {aq['firstQuestionCompared']} | Agreement {pct(aq['policyFirstQuestionAgreement'])}. |
| BM25 only vs semantic only vs hybrid | {retrieval['variants']['hybrid']['answerable']} answerable queries | Recall@1 {pct(retrieval['variants']['bm25']['recall@1'])} / {pct(retrieval['variants']['semantic']['recall@1'])} / {pct(retrieval['variants']['hybrid']['recall@1'])}. |
| Retrieval without a matched structured rule | {rules['n']} frozen matters | {pct(rules['withoutRulesUnsupportedApplicabilityExposure'])} retrieved sources lack a matched rule; proxy exposure only. |
| Deterministic vs Llama/Mistral | 9 generations per available model | Structural acceptance and fallback in `llm_comparison.md`; human usefulness difference N/A. |

Final conversations were recorded in source data, not newly produced by the app, and no unknown user fact was assumed. The rule proxy does not claim retrieval-only actually emitted an unsupported legal conclusion. A deterministic comparison cannot establish a quality gain without blinded judgments. Figures: `experiments/plots/adaptive_context.png`, `retrieval_comparison.png`, `llm_comparison.png`.
""")

    write("legal_coverage.md", """
# Phase 6 legal coverage and review status

The existing source policy remains unchanged: 6 of 18 sources and 4 of 11 provisions are eligible for retrieval. There is no eligible affirmative procedure, monetary penalty, or reviewed numeric speed-limit record. The malformed court-contest procedure is retained as `NOT_VERIFIED`; `OFF_NO_PUC` lacks a required source ID. A derived overlay proposes a reversible CSV alignment and a provisional AGE schema row, but neither promotes a legal record.

The three synthetic frozen cases each retrieve one eligible source with explicit Tamil Nadu jurisdiction and 2026-01-01 event date. The speed case has no MATCHED numerical rule; it can identify a potentially relevant provision but cannot decide a speed threshold or penalty. Insurance and registration have matched general-rule evidence in the frozen context. This does not certify their complete legal applicability. Production retrieval excludes missing or inapplicable date/jurisdiction material, and deterministic guidance carries explicit uncertainty.

Dataset review flags and official-looking links are not independent legal authentication. A qualified reviewer must check current legislation, amendments, state rules and procedures before asserting comprehensive legal coverage. No new legal source was marked independently reviewed in Phase 6.
""")

    failures = ["| `SYN_SPEED_01`, Llama | Cautious provision mention, no definite outcome | `DEFINITE_OUTCOME` and unlinked claim in English; fallback | Prompt and structural gate retained; unresolved model behavior |",
                "| `SYN_INSURANCE_01`, Llama | Only supported actions shown | Two model action strings were unsupported; omitted while answer accepted | Action allowlist applied |",
                "| Hindi, Llama frozen cases | Hindi answer and correct language tag | 3/3 rejected by language gate | Fallback; multilingual generation quality unresolved |",
                "| Grouped NLP test | Gold-consistent missing-slot sets | 1,570 false positive slots, mostly `USER_ROLE` and `VEHICLE_CLASS` | Schema/annotation mismatch remains; requirements retained |",
                "| `OFF_NO_PUC` | Source-backed penalty record | Missing source ID | Excluded; needs source review |",
                "| `SYN_INSURANCE_01`, Mistral English | Evidence-linked explanation | `UNLINKED_CLAIM` caused rejection | Deterministic fallback; prompt compliance remains weak |",
                "| Browser insurance case, refresh | Persisted matter without rendering error | Server rendered empty provider state while first client render read session storage, causing hydration mismatch | Provider restoration moved to post-hydration effect; Summary redirect waits for restoration |"]
    write("failure_analysis.md", "# Phase 6 failure analysis\n\n| Case | Expected | Observed and owner | Resolution |\n|---|---|---|---|\n" + "\n".join(failures) + "\n\nPer-case LLM and NLP predictions are retained under `experiments/predictions/`; rejected legal text was never displayed as guidance. No expert review was performed.\n")

    write("final_system_evaluation.md", f"""
# Phase 6 final system evaluation

The isolated local HTTP journey created a synthetic matter, persisted real NLP analysis, edited and confirmed facts, verified the user context, retrieved one admissible provision when date and jurisdiction were supplied, generated guidance, reloaded persisted guidance and completed the matter. A second synthetic matter answered an adaptive question with an explicit unknown, which remained in the persisted conversation. Stale revision and pre-verification guidance requests returned 409. Llama and Mistral end-to-end runs invoked real inference and fell back safely; a deterministic run completed without fallback. All five routes return HTTP 200 and build under Next.js 16.3.4. One interactive browser journey passed through Home, Understand, Verify, Guidance and Summary with real persisted backend state, confirmed five extracted facts, selected Llama, displayed one eligible source and safe fallback, and restored Summary on refresh without console errors. An earlier refresh exposed a hydration mismatch; restoring tab state after hydration fixed it. The print button and print CSS are present, but a completed PDF export and mobile visual QA were not verified.

| Evidence | Result |
|---|---|
| Grouped utterance split | {nlp['counts']['train']:,} train / {nlp['counts']['dev']:,} dev / {nlp['counts']['test']:,} test; previous test exposed. |
| Intent / entity / missing-slot F1 | {pct(nlp['intent']['macroF1'])} / {pct(nlp['entityExactSpan']['f1'])} / {pct(nlp['missingSlots']['f1'])}. |
| Language overall with abstentions | {pct(nlp['language']['overallAccuracy'])}, coverage {pct(nlp['language']['coverage'])}. |
| Hybrid retrieval | Recall@1 {pct(retrieval['variants']['hybrid']['recall@1'])}, MRR {retrieval['variants']['hybrid']['mrr']:.3f} on {retrieval['variants']['hybrid']['answerable']:,} admitted-positive queries. |
| Legal source coverage | 4 eligible provisions; no admissible numeric penalty, speed limit or affirmative procedure. |
| LLM safety | See `llm_comparison.md` for actual accepted/fallback rates; semantic support remains unreviewed. |

The measured NLP and retrieval results are exploratory because reference labels are unreviewed and the earlier test partition was exposed. Browser observations are recorded in `experiments/metrics/phase6_browser_e2e.json`; isolated HTTP run details are in adjacent metrics files. The main functional limits are missing-slot precision, sparse legal coverage and multilingual model acceptance. No public deployment was attempted because matter endpoints have no authentication.
""")

    write("deployment_readiness.md", """
# Phase 6 deployment readiness

**Local demonstrator:** supported on the tested Apple M3, 16 GiB machine. Python 3.12.6, Node 24.11.1, npm 11.6.2, Next.js 16.3.4 and Ollama 0.35.1 were observed. The backend virtual environment, NLP artifacts and hybrid index are present. Ollama reported Llama at 2.5 GB and Mistral at 4.9 GB loaded, both 100% GPU with 4096 context during testing; these are model footprints, not measured total peak memory. The checkpoints were run sequentially and then released. The full tested startup and evaluation commands are in the root and backend READMEs.

**Online deployment:** not ready and not claimed. Persistent matter APIs have no user authentication or retention policy. A hosted architecture needs an authenticated frontend/API, private database and access-controlled model-serving host with sufficient RAM/storage; ordinary serverless hosting will not run both local checkpoints. Do not expose this backend or SQLite database to the public internet. No public URL exists.

**Dataset/legal gate:** original validator still reports two critical errors. The research overlay leaves one. Only four legal provisions are eligible; independent legal review is outstanding. Model weights and SQLite contents remain outside Git.
""")

    write("PHASE6_IMPLEMENTATION.md", """
# Phase 6 implementation record and viva architecture

Phase 6 repaired training/test vocabulary leakage, added a reproducible connected scenario/template split, evaluated NLP and three retrieval rankers, froze synthetic admissible evidence, ran controlled local LLM comparisons, tightened structured output and action handling, added offline ablations, and exercised an isolated persisted HTTP workflow. The original datasets and source admissibility policy were preserved. This is a working local research demonstrator with documented legal and evaluation gaps, not a publicly deployed legal service.

## Architecture in order

1. A lightweight character TF-IDF SVM identifies likely intent because it is reproducible on limited local hardware; a language baseline and script policy choose a language or abstain.
2. Rule-based extraction keeps exact original-text offsets. Normalization maps spans to dataset IDs. Intent-specific slot rules identify required context and unresolved conditional requirements.
3. Adaptive questions select missing slots; user answers, contradictions, edits and provenance persist in SQLite. The user must confirm facts and explicitly verify the structured situation before retrieval.
4. Hybrid RAG combines BM25 and multilingual semantic rankings over policy-eligible provisions. Date/jurisdiction gates and structured rule evaluation determine what may be said; a ranked match alone is not a legal conclusion.
5. Deterministic guidance builds source cards, uncertainties and next steps. Llama 3.2 3B or Mistral 7B may rewrite only a frozen eligible-evidence package. Schema, citation, language, numeric-claim and definite-outcome gates reject unsafe output; fallback preserves deterministic guidance.
6. Both models are compared on the same three synthetic matters × three languages. Offline ablations measure recorded context gain, ranker contribution and rule-exposure proxy; they do not yield one unified full-system score.

See `nlp_results.md`, `retrieval_results.md`, `llm_comparison.md`, `ablation_study.md`, `failure_analysis.md`, `legal_coverage.md`, `final_system_evaluation.md`, and `deployment_readiness.md` for measured evidence. Human review of legal support and multilingual usefulness, stronger missing-slot labels, additional eligible sources, completed PDF export, and mobile visual QA remain outside the completed evidence.
""")


if __name__ == "__main__":
    run()
