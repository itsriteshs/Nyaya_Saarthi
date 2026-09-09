import Link from "next/link";
import { LockKeyhole, Menu, UserRound } from "lucide-react";
import type { LanguageOption } from "@/types/nlp";

const progressItems = ["Understand", "Verify", "Guidance", "Summary"];

interface UnderstandHeaderProps {
  language: LanguageOption;
  currentStep: "understand" | "verify" | "guidance" | "summary";
}

export function UnderstandHeader({ language, currentStep }: UnderstandHeaderProps) {
  const currentIndex = ["understand", "verify", "guidance", "summary"].indexOf(currentStep);

  return (
    <header className="border-b border-[#DED7CA] bg-[#FBF8F1]">
      <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3 lg:hidden">
          <button
            type="button"
            aria-label="Open navigation"
            className="grid size-10 place-items-center rounded-md border border-[#DED7CA] text-[#071B3A]"
          >
            <Menu size={19} aria-hidden="true" />
          </button>
          <Link href="/" className="font-editorial text-2xl font-bold text-[#071B3A]">
            Nyaya<span className="text-[#A8752B]">Saarthi</span>
          </Link>
        </div>

        <div className="hidden items-center gap-2 lg:flex">
          {progressItems.map((item, index) => (
            <div key={item} className="flex items-center gap-2">
              <span
                className={
                  index === currentIndex
                    ? "grid size-7 place-items-center rounded-full bg-[#071B3A] text-xs font-extrabold text-white"
                    : index < currentIndex
                      ? "grid size-7 place-items-center rounded-full border border-[#647567] bg-[#EEF5ED] text-xs font-extrabold text-[#35533A]"
                    : "grid size-7 place-items-center rounded-full border border-[#DED7CA] text-xs font-extrabold text-[#6B665D]"
                }
              >
                {index < currentIndex ? "✓" : index + 1}
              </span>
              <span className={index === currentIndex ? "text-sm font-extrabold text-[#18150F]" : "text-sm font-bold text-[#6B665D]"}>
                {item}
              </span>
              {index < progressItems.length - 1 ? <span className="h-px w-8 bg-[#DED7CA]" aria-hidden="true" /> : null}
            </div>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-3">
          <span className="hidden items-center gap-2 rounded-md border border-[#DED7CA] px-3 py-2 text-xs font-extrabold text-[#4F4A42] sm:inline-flex">
            <LockKeyhole size={14} aria-hidden="true" />
            Secure & Private
          </span>
          <span className="rounded-md border border-[#DED7CA] px-3 py-2 text-xs font-extrabold capitalize text-[#4F4A42]">
            {language}
          </span>
          <span className="grid size-9 place-items-center rounded-full border border-[#DED7CA] bg-[#F7F3EA] text-[#071B3A]">
            <UserRound size={17} aria-hidden="true" />
          </span>
        </div>
      </div>
      <div className="grid grid-cols-4 border-t border-[#DED7CA] lg:hidden">
        {progressItems.map((item, index) => (
          <div key={item} className="px-2 py-2 text-center text-[0.7rem] font-extrabold text-[#6B665D]">
            <span className={index === currentIndex ? "text-[#071B3A]" : undefined}>
              {index < currentIndex ? "✓" : index + 1} {item}
            </span>
          </div>
        ))}
      </div>
    </header>
  );
}
