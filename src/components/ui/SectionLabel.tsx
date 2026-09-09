import { cn } from "@/lib/utils";

interface SectionLabelProps {
  items: string[];
  className?: string;
}

export function SectionLabel({ items, className }: SectionLabelProps) {
  return (
    <div
      className={cn(
        "inline-flex max-w-full flex-wrap items-center gap-2 rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 py-2 text-[0.72rem] font-extrabold uppercase text-[#6B665D]",
        className,
      )}
    >
      {items.map((item, index) => (
        <span key={item} className="inline-flex items-center gap-2">
          {index > 0 ? <span className="h-3 w-px bg-[#DED7CA]" aria-hidden="true" /> : null}
          {item}
        </span>
      ))}
    </div>
  );
}
