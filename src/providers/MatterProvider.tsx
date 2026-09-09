"use client";

import { createContext, useContext, useMemo, useState } from "react";
import { loadStoredMatter, saveStoredMatter } from "@/lib/matter-storage";
import type { MatterContext } from "@/types/matter";

interface MatterProviderValue {
  matter: MatterContext | null;
  setMatter: (matter: MatterContext | null) => void;
  updateMatter: (updater: (matter: MatterContext) => MatterContext) => void;
}

const MatterContextValue = createContext<MatterProviderValue | undefined>(undefined);

export function MatterProvider({ children }: { children: React.ReactNode }) {
  const [matter, setMatterState] = useState<MatterContext | null>(() => loadStoredMatter());

  function setMatter(nextMatter: MatterContext | null) {
    setMatterState(nextMatter);
    saveStoredMatter(nextMatter);
  }

  function updateMatter(updater: (matter: MatterContext) => MatterContext) {
    setMatterState((current) => {
      if (!current) {
        return current;
      }

      const nextMatter = updater(current);
      saveStoredMatter(nextMatter);
      return nextMatter;
    });
  }

  const value = useMemo(
    () => ({
      matter,
      setMatter,
      updateMatter,
    }),
    [matter],
  );

  return <MatterContextValue.Provider value={value}>{children}</MatterContextValue.Provider>;
}

export function useMatter() {
  const value = useContext(MatterContextValue);

  if (!value) {
    throw new Error("useMatter must be used inside MatterProvider");
  }

  return value;
}
