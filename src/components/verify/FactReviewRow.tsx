"use client";

import { Check, Pencil } from "lucide-react";
import { useState } from "react";
import { ProvenanceBadge } from "@/components/verify/ProvenanceBadge";
import type { MatterFact } from "@/types/matter";

interface FactReviewRowProps {
  fact: MatterFact;
  onConfirm: (factId: string) => void;
  onChange: (factId: string, value: string) => void;
}

export function FactReviewRow({ fact, onConfirm, onChange }: FactReviewRowProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(fact.value === "Not answered yet" ? "" : fact.value);

  function save() {
    onChange(fact.id, value);
    setEditing(false);
  }

  return (
    <div className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-3">
      <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-start">
        <div>
          <p className="text-sm font-bold text-[#6B665D]">{fact.label}</p>
          {editing ? (
            <input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              className="mt-2 min-h-10 w-full rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 text-sm font-semibold text-[#18150F]"
            />
          ) : (
            <p className="mt-1 text-sm font-extrabold text-[#18150F]">{fact.value}</p>
          )}
        </div>
        <ProvenanceBadge provenance={fact.provenance} />
      </div>

      <div className="mt-3 flex flex-wrap gap-2 border-t border-[#DED7CA] pt-3">
        {fact.requiresConfirmation && !editing ? (
          <button
            type="button"
            className="inline-flex min-h-9 items-center gap-2 rounded-md border border-[#C49A55]/70 bg-[#F4E8D3] px-3 text-xs font-extrabold text-[#7A521F]"
            onClick={() => onConfirm(fact.id)}
          >
            <Check size={14} aria-hidden="true" />
            Confirm
          </button>
        ) : null}
        {editing ? (
          <button
            type="button"
            className="inline-flex min-h-9 items-center gap-2 rounded-md border border-[#071B3A] bg-[#071B3A] px-3 text-xs font-extrabold text-white"
            onClick={save}
          >
            <Check size={14} aria-hidden="true" />
            Save
          </button>
        ) : null}
        <button
          type="button"
          className="inline-flex min-h-9 items-center gap-2 rounded-md border border-[#DED7CA] px-3 text-xs font-extrabold text-[#071B3A]"
          onClick={() => setEditing((current) => !current)}
        >
          <Pencil size={14} aria-hidden="true" />
          Change
        </button>
      </div>
    </div>
  );
}
