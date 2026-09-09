"use client";

import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { NLPPreview } from "@/components/home/NLPPreview";
import { QuickTopics } from "@/components/home/QuickTopics";
import { SituationInput } from "@/components/home/SituationInput";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { defaultSituation } from "@/data/examples";
import { motorLawTopics } from "@/data/motor-law-topics";
import { createMatterContext } from "@/lib/mock-context-engine";
import { analyzeSituation } from "@/lib/mock-nlp";
import { useMatter } from "@/providers/MatterProvider";
import type { LanguageOption, TopicId } from "@/types/nlp";

export function HeroSection() {
  const router = useRouter();
  const { setMatter } = useMatter();
  const [situation, setSituation] = useState("");
  const [analysisInput, setAnalysisInput] = useState(defaultSituation);
  const [language, setLanguage] = useState<LanguageOption>("auto");
  const [activeTopic, setActiveTopic] = useState<TopicId>("traffic");

  const activeTopicData =
    motorLawTopics.find((topic) => topic.id === activeTopic) ?? motorLawTopics[0];

  const preview = useMemo(() => analyzeSituation(analysisInput), [analysisInput]);

  function handleSituationChange(value: string) {
    setSituation(value);
    setAnalysisInput(value.trim() ? value : activeTopicData.example);
  }

  function handleExampleSelect(example: string) {
    setSituation(example);
    setAnalysisInput(example);
  }

  function handleTopicSelect(topic: TopicId) {
    const selected = motorLawTopics.find((item) => item.id === topic);
    setActiveTopic(topic);

    if (!situation.trim() && selected) {
      setAnalysisInput(selected.example);
    }
  }

  function handleSubmit() {
    const nextInput = situation.trim() || activeTopicData.example;
    setSituation(nextInput);
    setAnalysisInput(nextInput);
    setMatter(createMatterContext(nextInput, language));
    router.push("/understand");
  }

  function handleReset() {
    setSituation("");
    setLanguage("auto");
    setActiveTopic("traffic");
    setAnalysisInput(defaultSituation);
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
            facts, asks only for missing details, and helps you reach verified Motor Vehicle Law
            guidance.
          </p>

          <SituationInput
            value={situation}
            language={language}
            placeholder={activeTopicData.placeholder}
            onChange={handleSituationChange}
            onLanguageChange={setLanguage}
            onExampleSelect={handleExampleSelect}
            onReset={handleReset}
            onSubmit={handleSubmit}
          />

          <QuickTopics activeTopic={activeTopic} onSelect={handleTopicSelect} />
        </div>

        <div className="relative">
          <div className="absolute -right-8 -top-8 hidden h-40 w-40 border border-[#C49A55]/35 lg:block" aria-hidden="true" />
          <NLPPreview result={preview} />
          <div className="mt-5 flex items-center gap-3 border-l-2 border-[#A8752B] pl-4 text-sm font-bold text-[#6B665D]">
            <ArrowRight size={17} aria-hidden="true" />
            Understand first. Legal retrieval comes after verified context.
          </div>
        </div>
      </div>
    </section>
  );
}
