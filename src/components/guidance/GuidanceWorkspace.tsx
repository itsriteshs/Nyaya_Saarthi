"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { DirectAnswer } from "@/components/guidance/DirectAnswer";
import { FactLawMapping } from "@/components/guidance/FactLawMapping";
import { GuidanceRail } from "@/components/guidance/GuidanceRail";
import { LegalSources } from "@/components/guidance/LegalSources";
import { NextSteps } from "@/components/guidance/NextSteps";
import { SituationSnapshot } from "@/components/guidance/SituationSnapshot";
import { Button } from "@/components/ui/Button";
import { mockLegalRetrieval } from "@/lib/mock-legal-retrieval";
import { getMatter } from "@/lib/api/matters";
import { completeMatter, generateGuidance, generateExplanation, getLegalStatus, getModels } from "@/lib/api/legal";
import type { ModelChoice, OutputLanguage } from "@/lib/api/legal";
import { useMatter } from "@/providers/MatterProvider";

export function GuidanceWorkspace() {
  const router = useRouter();
  const { matter, restored, setMatter } = useMatter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [modelChoice, setModelChoice] = useState<ModelChoice>(() => {
    const selected = matter?.guidance?.metadata?.requestedModel;
    return selected === "llama3.2-3b" || selected === "mistral-7b" ? selected : "deterministic";
  });
  const [outputLanguage, setOutputLanguage] = useState<OutputLanguage>(() => {
    const selected = matter?.guidance?.metadata?.requestedLanguage;
    return selected === "english" || selected === "hindi" || selected === "hinglish" ? selected : preferredLanguage(matter);
  });
  const [modelStatuses, setModelStatuses] = useState<Record<string, boolean>>({});
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const operation = useRef("");

  const guidance = matter?.guidance;
  const verified = matter?.stage === "USER_VERIFIED" || matter?.stage === "GUIDANCE_GENERATED" || matter?.stage === "COMPLETED";

  useEffect(() => {
    getModels().then((result) => {
      setModelStatuses(Object.fromEntries(result.models.map((model) => [model.id, model.available])));
    }).catch(() => setModelStatuses({})).finally(() => setModelsLoaded(true));
  }, []);

  useEffect(() => {
    if (!matter?.nlpAnalysis || !matter.revision) return;
    const key = `${matter.id}:${matter.revision}`;
    if (operation.current === key) return;
    operation.current = key;
    setBusy(true);
    getMatter(matter.id).then(async (stored) => {
      if (stored.stage === "USER_VERIFIED") {
        const catalog = await getModels().catch(() => null);
        const preferred = catalog?.models.find((model) => model.default && model.available);
        if (preferred) {
          const language = preferredLanguage(stored);
          setModelChoice(preferred.id); setOutputLanguage(language);
          return generateExplanation(stored.id, stored.revision, preferred.id, language);
        }
        return generateExplanation(stored.id, stored.revision, "deterministic", preferredLanguage(stored));
      }
      if (stored.guidance) {
        const selected = stored.guidance.metadata?.requestedModel;
        setModelChoice(selected === "llama3.2-3b" || selected === "mistral-7b" ? selected : "deterministic");
        const language = stored.guidance.metadata?.requestedLanguage;
        setOutputLanguage(language === "hindi" || language === "hinglish" ? language : "english");
        const status = await getLegalStatus();
        if (!status.index.indexVersion) throw new Error("Legal index is unavailable; rebuild it before viewing guidance");
        if (stored.guidance.metadata?.indexVersion !== status.index.indexVersion) return generateGuidance(stored.id, stored.revision);
      }
      return stored;
    }).then((stored) => {
      if (stored) { setMatter(stored); setError(""); }
    }).catch((cause) => {
      setError(cause instanceof Error ? cause.message : "Guidance could not be loaded");
    }).finally(() => setBusy(false));
  }, [matter?.id, matter?.nlpAnalysis, matter?.revision, setMatter]);

  useEffect(() => {
    if (process.env.NEXT_PUBLIC_NYAYA_DEMO_MODE !== "true" || !matter || matter.nlpAnalysis || !verified || guidance) {
      return;
    }

    const timer = window.setTimeout(() => {
      const result = mockLegalRetrieval(matter);
      setMatter({
        ...matter,
        guidance: result,
        stage: "GUIDANCE_GENERATED",
      });
    }, 650);

    return () => window.clearTimeout(timer);
  }, [guidance, matter, setMatter, verified]);

  const verifiedFacts = useMemo(
    () => matter?.facts.filter((fact) => matter.nlpAnalysis ? fact.provenance === "USER_CONFIRMED" && fact.confirmed : fact.state !== "unknown") ?? [],
    [matter],
  );

  async function handleContinueToSummary() {
    if (!matter?.guidance) {
      return;
    }

    if (matter.nlpAnalysis && matter.revision && matter.stage === "GUIDANCE_GENERATED") {
      setBusy(true);
      try {
        const stored = await completeMatter(matter.id, matter.revision);
        setMatter(stored);
        router.push("/summary");
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "Summary could not be prepared");
      } finally { setBusy(false); }
      return;
    }
    if (!matter.nlpAnalysis) setMatter({ ...matter, stage: "COMPLETED" });
    router.push("/summary");
  }

  async function handleGenerate() {
    if (!matter?.revision || !matter.nlpAnalysis) return;
    setBusy(true); setError("");
    try {
      const stored = await generateExplanation(matter.id, matter.revision, modelChoice, outputLanguage, Boolean(matter.guidance));
      setMatter(stored);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Explanation could not be generated");
    } finally { setBusy(false); }
  }

  if (!restored) return <main className="p-6" aria-live="polite">Loading saved situation…</main>;

  if (!matter) {
    return (
      <RouteGuardMessage
        title="Your situation must be verified before legal guidance can be generated."
        text="Start from the intake page so NyayaSaarthi can build and verify the matter context."
        action="Start a Situation"
        onAction={() => router.push("/")}
      />
    );
  }

  if (!verified) {
    return (
      <RouteGuardMessage
        title="Your situation must be verified before legal guidance can be generated."
        text="Review the structured context first. Legal guidance begins only after user verification."
        action="Review Situation"
        onAction={() => router.push("/verify")}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#18150F] lg:grid lg:grid-cols-[248px_1fr]">
      <AppSidebar currentStep="guidance" />
      <div className="min-w-0">
        <UnderstandHeader language={matter.language} currentStep="guidance" />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="mb-5 rounded-lg border border-[#DED7CA] bg-[#FBF8F1] px-5 py-5 sm:px-6">
              <span className="inline-flex rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] px-3 py-1 text-xs font-extrabold uppercase text-[#7A521F]">
                Verified Context
              </span>
              <span className="ml-2 inline-flex rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-1 text-xs font-extrabold uppercase text-[#6B665D]">
                {matter.nlpAnalysis ? "Dataset-reviewed legal information" : "Prototype legal guidance"}
              </span>
              <h1 className="font-editorial mt-3 text-4xl font-bold leading-tight text-[#18150F] sm:text-5xl">
                Guidance for Your Situation
              </h1>
              <p className="mt-3 max-w-4xl text-sm font-semibold leading-6 text-[#6B665D] sm:text-base">
                Based on your confirmed facts, this page shows eligible dataset records and any
                limits on their applicability. Linked government pages have not been independently authenticated. Guidance covers the primary issue shown here; other concerns may need separate review.
              </p>
            </div>

            {matter.nlpAnalysis ? (
              <section className="mb-5 rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
                <p className="text-xs font-extrabold uppercase text-[#A8752B]">Explanation method</p>
                <div className="mt-3 flex flex-wrap items-end gap-3">
                  <label className="text-sm font-bold text-[#18150F]">Model
                    <select className="mt-1 block rounded-md border border-[#DED7CA] bg-white p-2" value={modelChoice} disabled={busy} onChange={(event) => setModelChoice(event.target.value as ModelChoice)}>
                      <option value="deterministic">Deterministic guidance</option>
                      <option value="llama3.2-3b" disabled={!modelStatuses["llama3.2-3b"]}>Llama 3.2 3B{modelsLoaded && !modelStatuses["llama3.2-3b"] ? " — unavailable" : ""}</option>
                      <option value="mistral-7b" disabled={!modelStatuses["mistral-7b"]}>Mistral 7B{modelsLoaded && !modelStatuses["mistral-7b"] ? " — unavailable" : ""}</option>
                    </select>
                  </label>
                  <label className="text-sm font-bold text-[#18150F]">Output language
                    <select className="mt-1 block rounded-md border border-[#DED7CA] bg-white p-2" value={outputLanguage} disabled={busy} onChange={(event) => setOutputLanguage(event.target.value as OutputLanguage)}>
                      <option value="english">English</option><option value="hindi">Hindi</option><option value="hinglish">Hinglish</option>
                    </select>
                  </label>
                  <Button onClick={handleGenerate} disabled={busy || (!modelsLoaded && modelChoice !== "deterministic") || (modelChoice !== "deterministic" && !modelStatuses[modelChoice])}>
                    {busy ? "Generating…" : guidance ? "Regenerate explanation" : "Generate explanation"}
                  </Button>
                </div>
                {guidance ? <p className="mt-3 text-sm font-semibold text-[#6B665D]">{guidance.metadata?.fallbackUsed ? `Deterministic fallback used (${guidance.metadata.failureReason ?? "model unavailable"}).` : guidance.metadata?.generationMethod === "LOCAL_LLM" ? `AI explanation by ${guidance.metadata.requestedModel === "llama3.2-3b" ? "Llama 3.2 3B" : "Mistral 7B"}.` : "Deterministic guidance."} Source records come from the legal knowledge base.</p> : null}
              </section>
            ) : null}

            {guidance && guidance.metadata?.generationMethod !== "LOCAL_LLM" && (guidance.metadata?.outputLanguage ?? "english") === "english" ? (
              <p className="mb-5 text-sm font-semibold leading-6 text-[#6B665D]">This deterministic explanation is in English. Hindi and Hinglish explanations require an available local model.</p>
            ) : null}
            {error ? <section role="alert" className="mb-5 rounded-lg border border-red-300 bg-white p-5 text-red-800">{error}<Button className="ml-3" onClick={() => window.location.reload()}>Retry loading</Button></section> : null}
            {!guidance || busy && matter.nlpAnalysis && matter.stage === "USER_VERIFIED" ? (
              <RetrievalLoading />
            ) : (
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
                <div className="space-y-5">
                  <DirectAnswer guidance={guidance} />
                  <SituationSnapshot matter={matter} facts={verifiedFacts} />
                  <FactLawMapping guidance={guidance} />
                  <LegalSources sources={guidance.sources} />
                  <NextSteps steps={guidance.nextSteps} />
                  <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
                    <p className="text-xs font-extrabold uppercase text-[#A8752B]">
                      Summary Prepared
                    </p>
                    <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
                      Continue to Summary
                    </h2>
                    <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
                      Page 5 will use this same matter, verified facts, sources, uncertainties and
                      next steps to create the final guidance summary.
                    </p>
                    <Button className="mt-4" onClick={handleContinueToSummary} disabled={busy}>
                      Continue to Summary
                      <ArrowRight size={16} aria-hidden="true" />
                    </Button>
                  </section>
                </div>
                <GuidanceRail matter={matter} guidance={guidance} factCount={verifiedFacts.length} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function preferredLanguage(matter: { language: string; nlpAnalysis?: { language: { detectedLanguage: string } } } | null): OutputLanguage {
  const selected = matter?.language === "auto" ? matter.nlpAnalysis?.language.detectedLanguage : matter?.language;
  return selected === "hindi" || selected === "hinglish" ? selected : "english";
}

function RetrievalLoading() {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">
        Checking dataset-reviewed legal records...
      </p>
      <h2 className="font-editorial mt-3 text-4xl font-bold text-[#18150F]">
        Preparing grounded guidance
      </h2>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {["Matching confirmed facts", "Filtering source records", "Preparing grounded guidance"].map(
          (step) => (
            <div key={step} className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
              <p className="text-sm font-extrabold text-[#18150F]">{step}</p>
            </div>
          ),
        )}
      </div>
    </section>
  );
}

function RouteGuardMessage({
  title,
  text,
  action,
  onAction,
}: {
  title: string;
  text: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#F7F3EA] px-5 text-[#18150F]">
      <section className="max-w-xl rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-6">
        <p className="text-sm font-extrabold uppercase text-[#A8752B]">Guidance gate</p>
        <h1 className="font-editorial mt-3 text-4xl font-bold text-[#071B3A]">{title}</h1>
        <p className="mt-3 text-sm font-semibold leading-6 text-[#6B665D]">{text}</p>
        <Button className="mt-5" onClick={onAction}>
          {action}
        </Button>
      </section>
    </main>
  );
}
