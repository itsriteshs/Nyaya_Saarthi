import {
  CarFront,
  Gauge,
  IdCard,
  ReceiptText,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";
import { motorLawTopics } from "@/data/motor-law-topics";
import { cn } from "@/lib/utils";
import type { TopicId } from "@/types/nlp";

const iconMap = {
  traffic: Gauge,
  challan: ReceiptText,
  licence: IdCard,
  registration: CarFront,
  insurance: ShieldCheck,
  accident: TriangleAlert,
};

interface QuickTopicsProps {
  activeTopic: TopicId;
  onSelect: (topic: TopicId) => void;
}

export function QuickTopics({ activeTopic, onSelect }: QuickTopicsProps) {
  return (
    <div className="mt-5">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
        {motorLawTopics.map((topic) => {
          const Icon = iconMap[topic.id];
          const active = activeTopic === topic.id;

          return (
            <button
              key={topic.id}
              type="button"
              className={cn(
                "flex min-h-14 items-center gap-2 rounded-md border px-3 text-left text-sm font-extrabold transition-colors",
                active
                  ? "border-[#A8752B] bg-[#F4E8D3] text-[#18150F]"
                  : "border-[#DED7CA] bg-[#FBF8F1] text-[#4F4A42] hover:border-[#A8752B] hover:text-[#18150F]",
              )}
              aria-pressed={active}
              onClick={() => onSelect(topic.id)}
            >
              <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
              <span className="break-words">{topic.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
