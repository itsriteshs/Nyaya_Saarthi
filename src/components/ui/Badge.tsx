import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 py-1 text-xs font-extrabold uppercase text-[#6B665D]",
        className,
      )}
      {...props}
    />
  );
}
