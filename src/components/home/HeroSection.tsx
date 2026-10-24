"use client";

import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useRef, useState, useSyncExternalStore } from "react";
import { NLPPreview } from "@/components/home/NLPPreview";
import { QuickTopics } from "@/components/home/QuickTopics";
import { SituationInput } from "@/components/home/SituationInput";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { defaultSituation } from "@/data/examples";
import { motorLawTopics } from "@/data/motor-law-topics";
import { createMatterContext } from "@/lib/mock-context-engine";
import { analyzeSituation } from "@/lib/mock-nlp";
import { localReferenceDatetime } from "@/lib/api/nlp";
import { analyzeMatter, createMatter } from "@/lib/api/matters";
import { useMatter } from "@/providers/MatterProvider";
import type { MockNlpResult, TopicId } from "@/types/nlp";

const demoMode = process.env.NEXT_PUBLIC_NYAYA_DEMO_MODE === "true";
const emptyPreview: MockNlpResult = {
  inputText: "", detectedIssue: { label: "Awaiting analysis", description: "Describe your situation to see the model's findings." },
  extractedFacts: [], missingInformation: [], readiness: { found: 0, total: 0 },
  nextQuestion: "Enter a description to begin.", visibleSignals: [],
};

const subscribeToHydration = () => () => {};

export function HeroSection() {
  const interactive = useSyncExternalStore(subscribeToHydration, () => true, () => false);
  const router = useRouter();
  const { setMatter, intakeLanguage: language, setIntakeLanguage: setLanguage } = useMatter();
  const [situation, setSituation] = useState("");
  const [analysisInput, setAnalysisInput] = useState(demoMode ? defaultSituation : "");
  const [activeTopic, setActiveTopic] = useState<TopicId>("traffic");
  const submitInFlight = useRef(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const activeTopicData =
    motorLawTopics.find((topic) => topic.id === activeTopic) ?? motorLawTopics[0];

  const demoPreview = useMemo(() => demoMode ? analyzeSituation(analysisInput) : emptyPreview, [analysisInput]);
  // Real intake runs once on explicit submit, never while typing. Cancelling
  // a browser preview would not necessarily cancel the backend model request.
  const preview = demoMode ? demoPreview : emptyPreview;

  function handleSituationChange(value: string) {
    setError("");
    setSituation(value);
    setAnalysisInput(value);
  }

  function handleExampleSelect(example: string) {
    setError("");
    setSituation(example);
    setAnalysisInput(example);
  }

  function handleTopicSelect(topic: TopicId) {
    const selected = motorLawTopics.find((item) => item.id === topic);
    setActiveTopic(topic);

    if (demoMode && !situation.trim() && selected) {
      setAnalysisInput(selected.example);
    }
  }

  async function handleSubmit() {
    if (submitInFlight.current) return;
    const nextInput = situation.trim() || (demoMode ? activeTopicData.example : "");
    if (!nextInput) {
      setError("Please describe your situation or select an example before continuing.");
      return;
    }
    setSituation(nextInput);
    setAnalysisInput(nextInput);
    if (demoMode) {
      setMatter(createMatterContext(nextInput, language));
      router.push("/understand");
      return;
    }
    submitInFlight.current = true;
    setSubmitting(true);
    setError("");
    try {
      const created = await createMatter(nextInput, language);
      const analyzed = await analyzeMatter(created.id, created.revision, localReferenceDatetime());
      setMatter(analyzed);
      router.push("/understand");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not analyze your situation.");
    } finally {
      submitInFlight.current = false;
      setSubmitting(false);
    }
  }

  function handleReset() {
    setError("");
    setSituation("");
    setLanguage("auto");
    setActiveTopic("traffic");
    setAnalysisInput(demoMode ? defaultSituation : "");
  }

  return (
    <section id="home" className="relative overflow-hidden px-5 py-12 sm:px-8 lg:px-10 lg:py-16">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[minmax(0,1.02fr)_minmax(360px,0.82fr)] lg:items-center">
        <div className="max-w-3xl">
          <SectionLabel items={["AI-assisted", "Multilingual", "Motor Vehicle Law"]} />
          <h1 className="font-editorial mt-6 max-w-3xl text-5xl font-bold leading-none text-[#18150F] text-balance sm:text-6xl lg:text-7xl">
            Understand Your <span className="text-[#A8752B]">Road Situation</span> Before You
            Navigate the Law.
          </h1>
          <p className="mt-6 max-w-2xl text-lg font-semibold leading-8 text-[#4F4A42]">
            Describe what happened in your own words. NyayaSaarthi identifies the important
            facts, asks for missing details, and helps you reach source-grounded Motor Vehicle Law
            guidance after you verify your situation.
          </p>

          <SituationInput
            ready={interactive}
            value={situation}
            language={language}
            placeholder={activeTopicData.placeholder}
            onChange={handleSituationChange}
            onLanguageChange={(nextLanguage) => { setError(""); setLanguage(nextLanguage); }}
            onExampleSelect={handleExampleSelect}
            onReset={handleReset}
            onSubmit={handleSubmit}
            submitting={submitting}
          />
          {error ? <p role="alert" className="mt-3 text-sm font-bold text-red-700">{error}</p> : null}

          <QuickTopics activeTopic={activeTopic} onSelect={handleTopicSelect} />
        </div>

        <div className="relative">
          <div className="absolute -right-8 -top-8 hidden h-40 w-40 border border-[#C49A55]/35 lg:block" aria-hidden="true" />
          <NLPPreview result={preview} />
          {demoMode ? <p className="mt-2 text-sm font-bold text-[#7A521F]">Demo NLP preview</p> : null}
          <div className="mt-5 flex items-center gap-3 border-l-2 border-[#A8752B] pl-4 text-sm font-bold text-[#6B665D]">
            <ArrowRight size={17} aria-hidden="true" />
            Understand first. Legal retrieval comes after verified context.
          </div>
        </div>
      </div>
    </section>
  );
}
