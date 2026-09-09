import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-lg border border-[#DED7CA] bg-[#FBF8F1] shadow-[0_18px_60px_rgba(7,27,58,0.08)]",
        className,
      )}
      {...props}
    />
  );
}
