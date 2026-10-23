"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api/client";
import { useMatter } from "@/providers/MatterProvider";

type Value = null | boolean | number | string | Value[] | { [key: string]: Value };
type RecordValue = { [key: string]: Value };
function object(value: Value | undefined): RecordValue {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}
function list(value: Value | undefined): Value[] { return Array.isArray(value) ? value : []; }
function text(value: Value | undefined): string { return value == null ? "Not recorded" : String(value); }
function rate(value: Value | undefined) { return typeof value === "number" ? `${(100 * value).toFixed(1)}%` : "Unavailable"; }
function label(value: string) { return value.replace(/([a-z])([A-Z])/g, "$1 $2").replaceAll("_", " "); }

export function RecordedData({ value }: { value: Value | undefined }) {
  if (value == null) return <p className="text-[#6B665D]">Not recorded / unavailable.</p>;
  if (Array.isArray(value)) return value.length ? <ul className="space-y-3">{value.map((v, i) => <li key={i} className="rounded border border-[#DED7CA] p-3"><RecordedData value={v} /></li>)}</ul> : <p>None recorded.</p>;
  if (typeof value === "object") return <dl className="space-y-2">{Object.entries(value).map(([k,v]) => <div key={k} className="min-w-0"><dt className="text-sm font-bold text-[#6B665D]">{label(k)}</dt><dd className="break-words"><RecordedData value={v} /></dd></div>)}</dl>;
  if (typeof value === "string" && /^https?:\/\//.test(value)) return <a className="underline" href={value} target="_blank" rel="noreferrer">{value}</a>;
  return <span>{typeof value === "number" && !Number.isInteger(value) ? value.toFixed(4) : String(value)}</span>;
}
function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="min-w-0 rounded-xl border border-[#DED7CA] bg-[#FFFDFA] p-5 sm:p-7"><h2 className="mb-4 text-xl font-extrabold">{title}</h2>{children}</section>;
}
function Details({ title, value }: { title: string; value: Value | undefined }) {
  return <details className="mt-4 border-t border-[#DED7CA] pt-3"><summary className="cursor-pointer font-bold">{title}</summary><div className="mt-4"><RecordedData value={value} /></div></details>;
}
function Card({ title, value, note }: { title: string; value: string; note: string }) {
  return <div className="rounded-lg border border-[#DED7CA] bg-[#F5F0E7] p-4"><p className="text-sm font-bold">{title}</p><p className="my-2 text-2xl font-extrabold">{value}</p><p className="text-sm text-[#6B665D]">{note}</p></div>;
}

function TraceView({ trace }: { trace: RecordValue }) {
  const intent=object(trace.intent), attribution=object(intent.attribution), generation=object(trace.generation);
  const sources=list(trace.sources);
  return <div className="space-y-5">
    <Panel title="Recorded decision trace"><p className="mb-3">{text(trace.originalText)}</p><p className="text-sm">Matter {text(trace.matterId)} · revision {text(trace.revision)}. Stored observations, not hidden reasoning.</p><Details title="Trace limitations" value={trace.limitations}/></Panel>
    <div className="grid gap-5 lg:grid-cols-2">
      <Panel title="1. Language"><RecordedData value={trace.language}/><p className="mt-3 text-sm">The recorded evidence identifies the script policy or classifier used. A margin is not a probability.</p></Panel>
      <Panel title="2. Original intent prediction"><RecordedData value={Object.fromEntries(Object.entries(intent).filter(([k])=>k!=="attribution"))}/><Details title="User-selected workflow (separate from prediction)" value={trace.selectedWorkflow}/></Panel>
    </div>
    <Panel title="Inspectable intent features">
      {!attribution.classes ? <p>Feature attribution not recorded for this analysis. Old outputs are not re-explained using a newer model.</p> : <>
        <p>{text(attribution.method)}. {text(attribution.limitation)}</p>
        <div className="mt-4 grid gap-5 lg:grid-cols-3">{list(attribution.classes).map((item,i)=>{const row=object(item);return <div key={i} className="min-w-0"><h3 className="font-bold">{text(row.intent)} · margin {typeof row.score==="number"?row.score.toFixed(4):"unavailable"}</h3>{["positive","negative"].map(sign=><div key={sign} className="mt-3"><h4 className="text-sm font-bold">{sign==="positive"?"Supports this class":"Opposes this class"}</h4>{list(row[sign]).map((feature,j)=>{const f=object(feature);return <div key={j} className="flex justify-between gap-3 border-b border-[#DED7CA] py-1 text-sm"><code className="whitespace-pre-wrap break-all">{text(f.feature)}</code><span>{Number(f.contribution).toFixed(4)}</span></div>})}</div>)}</div>})}</div>
        <Details title="Exact input, intercepts, contribution sums and model fingerprint" value={attribution}/>
      </>}
    </Panel>
    <Panel title="3. Extracted facts and user review"><p className="mb-4">SLM interpretation is not user confirmation. Original quotes, normalized values and review status remain separate.</p><RecordedData value={trace.facts}/><Details title="Initial spans and offsets" value={trace.initialEntities}/><Details title="Extraction runtime and rejected mentions" value={trace.extraction}/></Panel>
    <Panel title="4. Why the next question was asked"><RecordedData value={trace.question}/><Details title="Missing slots" value={trace.missingSlots}/><Details title="Recorded conversation state" value={trace.conversation}/><Details title="Conversation messages (not a historical rationale reconstruction)" value={trace.messages}/></Panel>
    <Panel title="5. Retrieval and structured rules"><p className="mb-4">Ranking scores indicate ordering, not probabilities or legal applicability. Only stored fact-to-provision links are shown.</p><RecordedData value={trace.retrieval}/><Details title="Eligible sources and official links" value={trace.sources}/><Details title="Recorded fact-to-provision links" value={trace.mappings}/></Panel>
    <Panel title="6. Explanation and claim evidence"><p className="whitespace-pre-wrap">{text(trace.answer)}</p>
      <div className="mt-4 space-y-4">{list(trace.claims).map((item,i)=>{const c=object(item);return <article key={i} className="rounded border border-[#DED7CA] p-4"><p>{text(c.text)}</p><ul className="mt-2">{list(c.evidenceIds).map((id,j)=>{const source=object(sources.find(s=>object(s).evidenceId===id));return <li key={j}><span className="font-bold">{text(id)}</span> — {text(source.title)} {typeof source.sourceUrl==="string" && /^https?:\/\//.test(source.sourceUrl)?<a href={source.sourceUrl} className="underline" target="_blank" rel="noreferrer">Source</a>:null}</li>})}</ul></article>})}</div>
      {!trace.claims && <p className="mt-3">Sentence-level claim links not recorded. Deterministic source mappings are shown above when available.</p>}
      <div className="mt-4 grid gap-4 sm:grid-cols-3"><Card title="Generation method" value={text(generation.generationMethod)} note={text(generation.runtimeModel ?? generation.requestedModel)}/><Card title="Fallback reason" value={text(generation.failureReason)} note={generation.fallbackUsed===false?"No fallback recorded":"See recorded validation details"}/><Card title="Semantic entailment" value="Unavailable" note="Citation IDs do not prove semantic support or legal correctness."/></div>
      <Details title="Uncertainty and supported next steps" value={{uncertainties:trace.uncertainties??null,nextSteps:trace.nextSteps??null}}/>
      <Details title="Recorded model, language, validation, tokens and provenance" value={trace.generation}/>
    </Panel>
  </div>;
}

function Historical({ data }: { data: RecordValue }) {
  const ab=object(data.ablations), adaptive=object(ab.adaptiveQuestioning), retrieval=object(ab.retrieval), models=object(object(ab.llmVersusDeterministic).llm);
  return <Panel title="Historical Phase 6 results — exploratory">
    <p className="mb-5">{text(data.caveat)}</p>
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"><Card title="Recorded context coverage" value={`${rate(adaptive.withoutAdaptiveCapturedRate)} → ${rate(adaptive.recordedFinalCapturedRate)}`} note={`${text(adaptive.n)} recorded conversations; not current app-generated journeys.`}/><Card title="Hybrid Recall@1" value={rate(object(retrieval.hybrid)["recall@1"])} note={`${text(object(retrieval.hybrid).answerable)} answerable queries; ranking only.`}/><Card title="Rule-exposure proxy" value={rate(object(ab.ruleMatching).withoutRulesUnsupportedApplicabilityExposure)} note={`${text(object(ab.ruleMatching).n)} frozen synthetic matters; not emitted legal conclusions.`}/></div>
    <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[640px] text-left text-sm"><caption className="mb-2 text-left font-bold">Same historical queries, different rankers</caption><thead><tr>{["Ranker","Recall@1","Recall@3","Recall@5","MRR","Answerable N"].map(v=><th className="p-2" key={v}>{v}</th>)}</tr></thead><tbody>{Object.entries(retrieval).map(([k,v])=>{const r=object(v);return <tr key={k}>{[k,rate(r["recall@1"]),rate(r["recall@3"]),rate(r["recall@5"]),typeof r.mrr==="number"?r.mrr.toFixed(3):"Unavailable",text(r.answerable)].map((s,i)=><td key={i} className="border-t border-[#DED7CA] p-2">{s}</td>)}</tr>})}</tbody></table></div>
    <div className="mt-5 grid gap-4 sm:grid-cols-2">{Object.entries(models).map(([k,v])=><Card key={k} title={`${k}: structural acceptance`} value={rate(object(v).acceptedRate)} note={`N=${text(object(v).n)}; fallback ${rate(object(v).fallbackRate)}. Human usefulness and semantic support unmeasured.`}/>)}</div>
    <Details title="Exact historical component values and caveats" value={ab}/><Details title="Historical NLP results — exposed grouped test, pending labels" value={data.nlp}/><Details title="Retrieval protocol and exclusions" value={data.retrieval}/>
  </Panel>;
}

function RunView({ data }: { data: RecordValue }) {
  const nlp=object(data.nlp), probe=object(data.faithfulness);
  return <Panel title={`Development run: ${text(data.runId)}`}>
    <p>{text(data.timestamp)} · {text(data.split)} · {text(data.reviewStatus)}</p>
    <div className="my-4 grid gap-4 sm:grid-cols-3"><Card title="Development NLP cases" value={text(nlp.n)} note="Pending review; separate from reserved synthetic probe."/><Card title="Grouped test cases evaluated" value={text(nlp.testEvaluated)} note="Historical test artifacts are not rerun."/><Card title="Reserved synthetic probe" value={text(probe.n)} note="Template-related, unreviewed; not a production hallucination rate."/></div>
    {Object.keys(object(nlp.intent)).length>0 && <><h3 className="font-bold">Intent comparison</h3><div className="mt-3 grid gap-4 sm:grid-cols-3">{Object.entries(object(nlp.intent)).map(([k,v])=><Card key={k} title={label(k)} value={rate(object(v).accuracy)} note={`Macro-F1 ${rate(object(v).macroF1)}; N=${text(object(v).n)}`}/>)}</div><Details title="Paired comparison delta and uncertainty" value={nlp.intentDelta}/></>}
    {probe.perType && <><h3 className="mt-5 font-bold">Adversarial faithfulness screening by error type</h3><p className="mt-2 text-sm">{text(probe.threshold)}</p><div className="overflow-x-auto"><table className="mt-3 w-full min-w-[640px] text-left text-sm"><thead><tr>{["Error type","Corrupted N","Clean N","Detected","False positives","Disabled catch"].map(v=><th key={v} className="p-2">{v}</th>)}</tr></thead><tbody>{Object.entries(object(probe.perType)).map(([k,v])=>{const r=object(v);return <tr key={k}>{[label(k),text(r.corruptedN),text(r.cleanN),rate(r.detectionRate),rate(r.falsePositiveRate),rate(r.disabledDetectionRate)].map((s,i)=><td key={i} className="border-t border-[#DED7CA] p-2">{s}</td>)}</tr>})}</tbody></table></div></>}
    {data.retrieval && <><h3 className="mt-5 font-bold">Development ranking comparison</h3><RecordedData value={data.retrieval}/><Details title="Paired Recall@1 changes from hybrid" value={data.recall1DeltaFromHybrid}/></>}
    {data.adaptiveRecordedProxy && <><h3 className="mt-5 font-bold">Recorded adaptive context proxy</h3><RecordedData value={data.adaptiveRecordedProxy}/></>}
    <Details title="Run limitations" value={data.limitations}/>
    {data.generation && <><h3 className="mt-5 font-bold">Frozen-evidence generation comparison</h3><RecordedData value={data.generation}/></>}
    {data.extraction && <><h3 className="mt-5 font-bold">Reviewed paired extraction comparison</h3><RecordedData value={data.extraction}/></>}
    <Details title="NLP per-class results, confusion matrices, extraction and limitations" value={nlp}/>
    <Details title="Probe confidence intervals, selection and limitations" value={probe}/>
    <Details title="Unavailable comparisons and required data" value={data.unavailable}/>
    <Details title="Complete protocol, formulas, versions and artifact hashes" value={data}/>
  </Panel>;
}

export function ResearchDashboard() {
  const {matter}=useMatter();
  const [catalog,setCatalog]=useState<RecordValue|null>(null),[error,setError]=useState("");
  const [tab,setTab]=useState<"trace"|"studies">("trace"),[id,setId]=useState(""),[trace,setTrace]=useState<RecordValue|null>(null);
  const [traceError,setTraceError]=useState(""),[loading,setLoading]=useState(false),[run,setRun]=useState("");
  useEffect(()=>{const controller=new AbortController();apiRequest<RecordValue>("/api/v1/research/catalog",{signal:controller.signal}).then(setCatalog).catch(e=>{if(!controller.signal.aborted)setError(e.message)});return()=>controller.abort()},[]);
  async function loadTrace() {
    setLoading(true);setTraceError("");setTrace(null);
    try {setTrace(await apiRequest<RecordValue>(`/api/v1/research/matters/${encodeURIComponent(id||matter?.id||"")}/trace`));}
    catch(e){setTraceError(e instanceof Error?e.message:"Trace unavailable");}
    finally{setLoading(false);}
  }
  const runs=list(catalog?.runs), selected=object(runs.find(v=>object(v).id===run)??runs[runs.length-1]);
  return <main className="min-h-screen bg-[#FBF8F1] text-[#071B3A]">
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-8">
      <nav aria-label="Research navigation" className="flex flex-wrap gap-5 font-bold"><Link href="/">NyayaSaarthi Home</Link><Link href="/summary">Summary</Link></nav>
      <header><p className="text-sm font-extrabold uppercase text-[#A8752B]">Explainable AI · Research</p><h1 className="font-editorial mt-2 text-4xl font-bold">Follow the evidence. Inspect the limits.</h1><p className="mt-3 max-w-3xl">See recorded decisions and controlled component comparisons. These views describe system behavior; they do not certify legal correctness. Evaluations run offline.</p></header>
      <div role="group" aria-label="Research view" className="flex flex-wrap gap-3">{(["trace","studies"] as const).map(t=><button key={t} aria-pressed={tab===t} onClick={()=>setTab(t)} className={`min-h-11 rounded-md border border-[#DED7CA] px-5 py-3 font-bold ${tab===t?"bg-[#071B3A] text-white":"bg-white"}`}>{t==="trace"?"Matter explainability":"Ablation studies"}</button>)}</div>
      {tab==="trace"?<>
        <Panel title="Select a matter"><label htmlFor="research-matter" className="mb-2 block font-bold">Matter ID</label><div className="flex flex-col gap-3 sm:flex-row"><input id="research-matter" value={id} onChange={e=>setId(e.target.value)} placeholder={matter?.id??"Paste a saved matter ID"} className="min-w-0 flex-1 rounded border border-[#DED7CA] p-3"/><button disabled={loading||(!id&&!matter?.id)} onClick={loadTrace} className="rounded bg-[#071B3A] px-5 py-3 font-bold text-white disabled:opacity-50">{loading?"Loading trace…":"Inspect recorded trace"}</button></div><p className="mt-3 text-sm">{matter?"Leave blank to inspect the matter active in this tab.":"No active matter. Start a situation from Home or enter a saved ID."}</p></Panel>
        {traceError&&<p role="alert" className="rounded border border-red-300 p-4">{traceError}</p>}
        {trace&&<TraceView trace={trace}/>}
      </>:<>
        {error?<p role="alert">Research artifacts unavailable: {error}. Refresh to retry.</p>:!catalog?<p role="status">Loading research artifacts…</p>:<>
          <Panel title="How to read these results"><p>Each component uses its own documented cases and denominator. There is no combined quality score. Positive deltas are not always improvements: more unsupported facts or false alarms are worse.</p><RecordedData value={catalog.nli}/></Panel>
          {runs.length?<><label className="block font-bold" htmlFor="research-run">Development artifact</label><select id="research-run" value={run||text(selected.id)} onChange={e=>setRun(e.target.value)} className="max-w-full rounded border border-[#DED7CA] p-3">{runs.map(v=><option key={text(object(v).id)} value={text(object(v).id)}>{text(object(v).id)}</option>)}</select>{selected.summary?<RunView data={object(selected.summary)}/>:<p role="alert">Selected artifact is invalid or unavailable.</p>}</>:<Panel title="No Phase 7 results yet"><p>Run the documented offline development workflow. Missing results are not zero scores.</p></Panel>}
          <Historical data={object(catalog.historical)}/>
        </>}
      </>}
    </div>
  </main>;
}
