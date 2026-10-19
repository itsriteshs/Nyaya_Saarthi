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
import { completeMatter, generateGuidance, getLegalStatus } from "@/lib/api/legal";
import { useMatter } from "@/providers/MatterProvider";

export function GuidanceWorkspace() {
  const router = useRouter();
  const { matter, setMatter } = useMatter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const operation = useRef("");

  const guidance = matter?.guidance;
  const verified = matter?.stage === "USER_VERIFIED" || matter?.stage === "GUIDANCE_GENERATED" || matter?.stage === "COMPLETED";

  useEffect(() => {
    if (!matter?.nlpAnalysis || !matter.revision) return;
    const key = `${matter.id}:${matter.revision}`;
    if (operation.current === key) return;
    operation.current = key;
    setBusy(true);
    getMatter(matter.id).then(async (stored) => {
      if (stored.stage === "USER_VERIFIED") return generateGuidance(stored.id, stored.revision);
      if (stored.guidance) {
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
    if (!matter || matter.nlpAnalysis || !verified || guidance) {
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
                limits on their applicability. Linked government pages have not been independently authenticated.
              </p>
            </div>

            {error ? (
              <section role="alert" className="rounded-lg border border-red-300 bg-white p-5 text-red-800">{error}</section>
            ) : !guidance || busy && matter.nlpAnalysis && matter.stage === "USER_VERIFIED" ? (
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
