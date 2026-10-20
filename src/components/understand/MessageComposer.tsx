import { Send } from "lucide-react";
import type { FormEvent } from "react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

interface MessageComposerProps {
  disabled: boolean;
  onSend: (answer: string) => Promise<boolean> | void;
}

export function MessageComposer({ disabled, onSend }: MessageComposerProps) {
  const [value, setValue] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!value.trim()) {
      return;
    }

    const saved = await onSend(value);
    if (saved !== false) setValue("");
  }

  return (
    <form onSubmit={submit} className="sticky bottom-0 border-t border-[#DED7CA] bg-[#FBF8F1] p-4 sm:p-5">
      <label htmlFor="answer" className="sr-only">
        Type your answer
      </label>
      <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
        <textarea
          id="answer"
          rows={2}
          value={value}
          disabled={disabled}
          placeholder={disabled ? "Choose one of the options above." : "Type your answer..."}
          onChange={(event) => setValue(event.target.value)}
          className="min-h-16 w-full resize-none rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-4 py-3 text-sm font-semibold leading-6 text-[#18150F] placeholder:text-[#8A8378] disabled:bg-[#F1ECE2]"
        />
        <Button type="submit" disabled={disabled || !value.trim()}>
          <Send size={16} aria-hidden="true" />
          Send
        </Button>
      </div>
      <p className="mt-2 text-xs font-bold text-[#6B665D]">English, Hindi and Hinglish supported</p>
    </form>
  );
}
