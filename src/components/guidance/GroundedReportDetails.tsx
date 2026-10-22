import type { GuidanceResult } from "@/types/matter";

const reasons: Record<string, string> = {
  RUNTIME_UNREACHABLE: "The local model service could not be reached.",
  NOT_INSTALLED: "The selected model is not installed locally.",
  MODEL_NOT_INSTALLED: "The selected model is not installed locally.",
  INFERENCE_TIMEOUT: "The local model did not respond within the time limit.",
  INSUFFICIENT_ELIGIBLE_EVIDENCE: "No eligible source supports an answer for these confirmed facts. Relevant reviewed evidence is needed before drawing a legal conclusion.",
  UNLINKED_CLAIM: "The model's citations did not match its displayed legal statements.",
  UNKNOWN_EVIDENCE_ID: "The model cited a source outside the eligible evidence.",
  CLAIM_CITATION_INVALID: "A legal statement did not have a valid evidence reference.",
  UNSUPPORTED_SPEED_FIGURE: "The response contained a speed figure without permitted support or clear attribution to your confirmed report.",
  UNSUPPORTED_PENALTY: "The response included an unsupported penalty.",
  UNSUPPORTED_DEADLINE: "The response included an unsupported deadline.",
  DEFINITE_OUTCOME: "The response asserted a legal outcome the evidence cannot establish.",
  OUTPUT_LANGUAGE_MISMATCH: "The response did not match the requested language.",
  OUTPUT_LANGUAGE_CODE_MISMATCH: "The model returned a different language code from the one requested.",
  OUTPUT_LANGUAGE_TEXT_MISMATCH: "The model's answer text used the wrong language or script.",
  OUTPUT_SCHEMA_INVALID: "The model response did not match the required structure.",
  OUTPUT_TRUNCATED: "The model response was cut off.",
};

export function GroundedReportDetails({ guidance }: { guidance: GuidanceResult }) {
  const claims = guidance.metadata?.structuredOutput?.legalClaims ?? [];
  return <div className="mt-4 space-y-4 break-words text-sm leading-6">
    {guidance.metadata?.fallbackUsed ? <div role="status" className="rounded-md border border-[#DED7CA] p-3">
      <strong>Why a source-based fallback is shown</strong>
      {(guidance.metadata.failureReason ?? "UNKNOWN").split(",").map(code => <p key={code}>{reasons[code] ?? `The model response could not be safely accepted (${code}).`}</p>)}
    </div> : null}
    {claims.length ? <div><h3 className="font-bold">What the cited sources support</h3>{claims.map((claim, i) => <div key={i} className="mt-2">
      <p>{claim.text}</p>
      {claim.evidenceIds.map(id => { const source = guidance.sources.find(s => s.evidenceId === id);
        return source ? <a className="mr-3 underline" key={id} href={source.sourceUrl} target="_blank" rel="noreferrer">{source.title} · {id}</a> : <span key={id}>{id}</span>;
      })}
    </div>)}</div> : null}
    <div><h3 className="font-bold">What cannot yet be concluded</h3>{guidance.uncertainties.map((text, i) => <p key={i}>{text}</p>)}</div>
    <div><h3 className="font-bold">Practical next steps</h3>{guidance.nextSteps.length ? guidance.nextSteps.map(step => <p key={step.id}>{step.title}: {step.description}</p>) : <p>No source-backed procedure is available for this situation in the reviewed records. Keep any official notice and its cited provision for a source check or qualified review; this app cannot verify a fine amount or response deadline here.</p>}</div>
  </div>;
}
