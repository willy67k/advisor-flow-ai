import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { useAuthStore } from "../stores/authStore";

interface HydrationGateProps {
  readonly children: ReactNode;
}

/**
 * Persisted tokens load asynchronously; avoids redirecting before rehydrate finishes.
 */
export function HydrationGate({ children }: HydrationGateProps) {
  const [ready, setReady] = useState(() => useAuthStore.persist.hasHydrated());

  useEffect(() => {
    const unsub = useAuthStore.persist.onFinishHydration(() => setReady(true));
    if (!useAuthStore.persist.hasHydrated()) {
      void useAuthStore.persist.rehydrate();
    }
    return unsub;
  }, []);

  if (!ready) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-950 text-sm font-medium tracking-wide text-slate-400">Loading…</div>;
  }

  return <>{children}</>;
}
