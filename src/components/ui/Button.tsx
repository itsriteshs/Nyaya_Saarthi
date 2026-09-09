import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "border-[#071B3A] bg-[#071B3A] text-white hover:bg-[#102A52] hover:border-[#102A52]",
  secondary:
    "border-[#DED7CA] bg-[#FBF8F1] text-[#071B3A] hover:border-[#A8752B] hover:text-[#18150F]",
  ghost:
    "border-transparent bg-transparent text-[#18150F] hover:bg-[#EFE8DA]",
};

export function Button({
  className,
  variant = "primary",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex min-h-11 items-center justify-center gap-2 rounded-md border px-4 text-sm font-extrabold transition-colors disabled:cursor-not-allowed disabled:opacity-55",
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  );
}
