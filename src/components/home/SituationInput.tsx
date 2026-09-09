import { ArrowRight, Mic, RotateCcw } from "lucide-react";
import type { FormEvent } from "react";
import { Button } from "@/components/ui/Button";
import { examplePrompts } from "@/data/examples";
import { cn } from "@/lib/utils";
import type { LanguageOption } from "@/types/nlp";

const languageOptions: Array<{ value: LanguageOption; label: string }> = [
  { value: "auto", label: "Auto" },
  { value: "english", label: "English" },
  { value: "hindi", label: "हिन्दी" },
  { value: "hinglish", label: "Hinglish" },
];

interface SituationInputProps {
  value: string;
  language: LanguageOption;
  placeholder: string;
  onChange: (value: string) => void;
  onLanguageChange: (language: LanguageOption) => void;
  onExampleSelect: (example: string) => void;
  onReset: () => void;
  onSubmit: () => void;
}

export function SituationInput({
  value,
  language,
  placeholder,
  onChange,
  onLanguageChange,
  onExampleSelect,
  onReset,
  onSubmit,
}: SituationInputProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mt-8 rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-4 shadow-[0_18px_70px_rgba(7,27,58,0.08)] sm:p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label htmlFor="situation" className="text-sm font-extrabold uppercase text-[#18150F]">
          Explain your situation
        </label>
        <button
          type="button"
          className="inline-flex min-h-10 items-center gap-2 rounded-md border border-[#DED7CA] px-3 text-sm font-bold text-[#6B665D] transition-colors hover:border-[#A8752B] hover:text-[#18150F]"
          onClick={onReset}
        >
          <RotateCcw size={16} aria-hidden="true" />
          Reset
        </button>
      </div>

      <textarea
        id="situation"
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        rows={4}
        className="mt-3 min-h-36 w-full resize-y rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-4 py-4 text-base font-semibold leading-7 text-[#18150F] placeholder:text-[#8A8378]"
      />

      <div className="mt-4 grid gap-4 border-t border-[#DED7CA] pt-4 xl:grid-cols-[1fr_auto] xl:items-center">
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-sm font-extrabold text-[#6B665D]">Language:</span>
          {languageOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className={cn(
                "min-h-10 rounded-md border px-3 text-sm font-extrabold transition-colors",
                language === option.value
                  ? "border-[#071B3A] bg-[#071B3A] text-white"
                  : "border-[#DED7CA] bg-[#FBF8F1] text-[#18150F] hover:border-[#A8752B]",
              )}
              onClick={() => onLanguageChange(option.value)}
            >
              {option.label}
            </button>
          ))}
          <button
            type="button"
            className="ml-0 inline-flex min-h-10 items-center gap-2 rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 text-sm font-extrabold text-[#18150F] transition-colors hover:border-[#A8752B] md:ml-2"
            aria-label="Speak your situation"
          >
            <Mic size={16} aria-hidden="true" />
            Speak
          </button>
        </div>

        <Button type="submit" className="w-full px-5 xl:w-auto">
          Understand My Situation
          <ArrowRight size={17} aria-hidden="true" />
        </Button>
      </div>

      <div className="mt-5">
        <p className="text-sm font-extrabold text-[#6B665D]">Not sure how to start?</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {examplePrompts.map((example) => (
            <button
              key={example.id}
              type="button"
              className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-2 text-left text-sm font-bold text-[#18150F] transition-colors hover:border-[#A8752B] hover:bg-[#F5EFE2]"
              onClick={() => onExampleSelect(example.text)}
            >
              {example.text}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}
