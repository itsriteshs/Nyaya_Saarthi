import { Scale, UserRound } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ConversationMessage as ConversationMessageType } from "@/types/matter";

interface ConversationMessageProps {
  message: ConversationMessageType;
}

export function ConversationMessage({ message }: ConversationMessageProps) {
  const user = message.speaker === "user";

  return (
    <article className={cn("flex gap-3", user && "justify-end")}>
      {!user ? (
        <span className="mt-1 grid size-9 shrink-0 place-items-center rounded-md border border-[#DED7CA] bg-[#F7F3EA] text-[#071B3A]">
          <Scale size={17} aria-hidden="true" />
        </span>
      ) : null}
      <div
        className={cn(
          "max-w-[760px] rounded-lg border px-4 py-3",
          user
            ? "border-[#C9D2DD] bg-[#EEF2F5] text-[#18150F]"
            : "border-[#DED7CA] bg-[#FFFDF8] text-[#18150F]",
        )}
      >
        <p className="mb-1 text-xs font-extrabold uppercase text-[#6B665D]">
          {user ? "User" : "NyayaSaarthi"}
        </p>
        <p className="text-sm font-semibold leading-6 sm:text-base">{message.text}</p>
      </div>
      {user ? (
        <span className="mt-1 grid size-9 shrink-0 place-items-center rounded-md border border-[#C9D2DD] bg-[#EEF2F5] text-[#071B3A]">
          <UserRound size={17} aria-hidden="true" />
        </span>
      ) : null}
    </article>
  );
}
