"use client";
import {useEffect,useState} from "react";
import {apiRequest} from "@/lib/api/client";
import {RecordedData} from "./ResearchDashboard";
type V=null|boolean|number|string|V[]|{[k:string]:V};
type R={[k:string]:V};
const obj=(v:V|undefined):R=>v&&typeof v==="object"&&!Array.isArray(v)?v:{};
const arr=(v:V|undefined):V[]=>Array.isArray(v)?v:[];
function Bars({data}:{data:R}){
 const nlp=obj(data.nlp),dataset=obj(data.dataset),retrieval=obj(data.retrieval);
 const values=Object.keys(obj(nlp.intent)).length?Object.entries(obj(nlp.intent)).map(([k,v])=>[k,obj(v).accuracy] as const):Object.keys(retrieval).length?Object.entries(retrieval).map(([k,v])=>[k,obj(v)["recall@1"]] as const):Object.entries(obj(dataset.languages));
 const valid=values.filter((v):v is [string,number]=>typeof v[1]==="number");
 const max=Math.max(...valid.map(v=>v[1]),1);
 return valid.length?<figure className="rounded border p-4"><figcaption className="mb-3 font-bold">{Object.keys(obj(nlp.intent)).length?"Development intent accuracy":Object.keys(retrieval).length?"Development Recall@1":"Annotated language counts"}</figcaption>{valid.map(([k,v])=><div key={k} className="mb-3"><div className="flex justify-between gap-3 text-sm"><span>{k}</span><span>{v.toFixed(3)}</span></div><svg role="img" aria-label={`${k}: ${v}`} viewBox="0 0 400 16" className="h-4 w-full"><title>{k}: {v}; from stored metrics</title><rect width={400*v/max} height="16" fill="#17385c"/></svg></div>)}<p className="text-xs">N={String(nlp.n??obj(retrieval.hybrid).answerable??dataset.utterances)} · {String(data.timestamp)} · source: metrics.json · pending review</p></figure>:null;
}
const sections=["Overview","Dataset Intelligence","NLP Benchmark","Conversation Intelligence","Legal Retrieval","LLM Benchmark","RAG versus No RAG","Ablation Laboratory","Explainable AI","Reliability and Testing","IEEE Research Export"];
const keyMap:Record<string,string[]>={"Dataset Intelligence":["dataset","integrity"],"NLP Benchmark":["nlp","entities"],"Conversation Intelligence":["adaptiveRecordedProxy"],"Legal Retrieval":["retrieval"],"LLM Benchmark":["generation"],"RAG versus No RAG":["rag"],"Ablation Laboratory":["faithfulness","recall1DeltaFromHybrid","intentDelta"],"Explainable AI":["lime"],"Reliability and Testing":["testing"]};
export function AdvancedConsole(){
 const [catalog,setCatalog]=useState<R|null>(null),[section,setSection]=useState("Overview"),[run,setRun]=useState(""),[error,setError]=useState("");
 const [exports,setExports]=useState<string[]>([]);
 const [examples,setExamples]=useState<V[]>([]),[caseId,setCaseId]=useState("0"),[language,setLanguage]=useState("all"),[model,setModel]=useState("all");
 useEffect(()=>{const c=new AbortController();apiRequest<R>("/api/v1/research/catalog",{signal:c.signal}).then(setCatalog).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[]);
 const runs=arr(catalog?.runs).map(obj).filter(r=>Object.keys(keyMap[section]??{}).length===0||(keyMap[section]??[]).some(k=>obj(r.summary)[k]!=null));
 const selected=runs.find(r=>r.id===run)??runs[runs.length-1];const data=obj(selected?.summary);const selectedId=String(selected?.id??"");
 useEffect(()=>{if(!selectedId)return;const c=new AbortController();apiRequest<R>(`/api/v1/research/runs/${encodeURIComponent(selectedId)}/examples`,{signal:c.signal}).then(v=>setExamples(arr(v.cases))).catch(()=>setExamples([]));return()=>c.abort()},[selectedId]);
 useEffect(()=>{if(!selectedId)return;const c=new AbortController();apiRequest<R>(`/api/v1/research/runs/${encodeURIComponent(selectedId)}/exports`,{signal:c.signal}).then(v=>setExports(arr(v.files).map(String))).catch(()=>setExports([]));return()=>c.abort()},[selectedId]);
 const filtered=examples.filter(v=>{const r=obj(v);return(language==="all"||r.language===language||r.goldLanguage===language)&&(model==="all"||r.model===model||obj(r.intent)[model]!=null)});
 const current=obj(filtered[Number(caseId)]??filtered[0]);
 function download(){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify({run:selectedId,case:current},null,2)],{type:"application/json"}));a.download="sanitized-research-selection.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
 return <div className="grid min-w-0 gap-5 lg:grid-cols-[240px_1fr]"><nav aria-label="Evaluation sections" className="flex flex-wrap gap-2 lg:flex-col">{sections.map((s,i)=><button className={`rounded border border-[#DED7CA] p-3 text-left text-sm font-bold ${section===s?"bg-[#071B3A] text-white":"bg-white"}`} aria-pressed={section===s} onClick={()=>{setSection(s);setRun("");setCaseId("0")}} key={s}>{String(i+1).padStart(2,"0")} · {s}</button>)}</nav>
 <section className="min-w-0 space-y-4 rounded-xl border border-[#DED7CA] bg-white p-5"><h2 className="text-2xl font-extrabold">{section}</h2>{error?<p role="alert">{error}</p>:!catalog?<p role="status">Loading stored experiments…</p>:<>
 <p className="text-sm">Development diagnostics · labels pending review · no aggregate legal-quality score.</p>
 {section==="Overview"&&<p>Local SLM intake, character SVM intent, user verification, eligible hybrid retrieval, rule matching, and local Llama/Mistral explanations. Qwen is not enabled. Select a section to inspect stored runs.</p>}
 <label className="block font-bold">Experiment<select aria-label="Experiment" value={selectedId} onChange={e=>{setRun(e.target.value);setCaseId("0")}} className="mt-2 block max-w-full rounded border p-3">{runs.map(r=><option key={String(r.id)} value={String(r.id)}>{String(r.id)}</option>)}</select></label>
 <p className="text-sm">{String(data.timestamp??"No run date")} · {String(data.split??"No matching experiment")}</p>
 <Bars data={data}/>
 {section==="IEEE Research Export"&&<ul>{exports.map(f=><li key={f}><a className="underline" href={`${process.env.NEXT_PUBLIC_API_BASE_URL??"http://127.0.0.1:8000"}/api/v1/research/runs/${encodeURIComponent(selectedId)}/exports/${encodeURIComponent(f)}`}>{f}</a></li>)}</ul>}
 {runs.length===0?<p>Not measured — matching experiment or reviewed labels required.</p>:(keyMap[section]??[]).map(k=><details key={k} open><summary className="font-bold">{k}</summary><div className="mt-3 max-h-[65vh] overflow-auto"><RecordedData value={data[k]}/></div></details>)}
 {section==="Reliability and Testing"&&!data.testing&&<p>The executable backend and browser suites are documented in the implementation report. A live test-pass score is unavailable until a machine-readable test report is imported; a model judge was not used.</p>}
 {section==="IEEE Research Export"&&<p>Publication files are generated offline by phase7_export.py from the same metrics.json files. CSV tables, PNG/SVG figures and captions are saved in each run’s publication directory. Missing semantic metrics remain unavailable.</p>}
 <details><summary className="font-bold">Protocol and limitations</summary><div className="max-h-96 overflow-auto"><RecordedData value={{runId:data.runId??null,limitations:data.limitations??null,unavailable:data.unavailable??null,command:data.command??null}}/></div></details>
 <h3 className="font-bold">Sanitized example explorer</h3><div className="flex flex-wrap gap-3"><label>Language<select aria-label="Example language" value={language} onChange={e=>{setLanguage(e.target.value);setCaseId("0")}} className="block rounded border p-2">{["all","English","Hindi","Hinglish","english","hindi","hinglish"].map(v=><option key={v}>{v}</option>)}</select></label><label>Model<select aria-label="Example model" value={model} onChange={e=>{setModel(e.target.value);setCaseId("0")}} className="block rounded border p-2">{["all","linear_svc","logistic_regression","multinomial_nb","llama3.2-3b","mistral-7b","deterministic"].map(v=><option key={v}>{v}</option>)}</select></label><label>Case<select aria-label="Evaluation case" value={caseId} onChange={e=>setCaseId(e.target.value)} className="block max-w-52 rounded border p-2">{filtered.map((v,i)=><option key={i} value={i}>{String(obj(v).id??obj(v).caseId??i)} {String(obj(v).condition??"")}</option>)}</select></label></div>
 {filtered.length?<><button onClick={download} className="rounded border px-4 py-2 font-bold">Export selected record</button>{typeof current.input==="string"&&arr(current.runs).length>0&&<p className="rounded border p-3 leading-8">{current.input.split(/(\s+)/).map((word,i)=>{if(!word.trim())return word;const position=Math.floor(i/2);const term=arr(obj(arr(current.runs)[0]).tokens).map(obj).find(t=>t.position===position);return <mark key={i} tabIndex={0} title={`SVM surrogate weight ${String(term?.weight??"not recorded")}; not legal evidence`} className={Number(term?.weight)>0?"bg-[#E4EEE5]":"bg-[#F4E3DB]"}>{word}</mark>})}</p>}<div className="max-h-[60vh] overflow-auto"><RecordedData value={current}/></div></>:<p>No public examples match these filters. Private matters are not exported here.</p>}
 </> }</section></div>
}
