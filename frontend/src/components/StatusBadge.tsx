import { useEffect, useState } from "react";
import { Wifi, WifiOff } from "lucide-react";

import { getHealth, type HealthResponse } from "../lib/api";
import { cn } from "../lib/utils";

type HealthState = {
  online: boolean;
  loading: boolean;
  details: HealthResponse | null;
};

export function StatusBadge() {
  const [health, setHealth] = useState<HealthState>({
    online: false,
    loading: true,
    details: null,
  });

  useEffect(() => {
    let mounted = true;

    const poll = async () => {
      try {
        const res = await getHealth();
        if (!mounted) return;
        setHealth({
          online: true,
          loading: false,
          details: res,
        });
      } catch {
        if (!mounted) return;
        setHealth((prev) => ({
          online: false,
          loading: false,
          details: prev.details,
        }));
      }
    };

    void poll();
    const interval = window.setInterval(() => {
      void poll();
    }, 10000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  const isOnline = health.online;

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium",
        isOnline
          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
          : "border-red-500/40 bg-red-500/10 text-red-300"
      )}
      title={health.details ? `Model: ${health.details.model_version}` : "API status"}
    >
      <span
        className={cn(
          "inline-block h-2.5 w-2.5 rounded-full",
          isOnline ? "animate-pulse bg-emerald-400" : "bg-red-400"
        )}
      />
      <span className="hidden sm:inline">API Status:</span>
      <span>{health.loading ? "Checking" : isOnline ? "Online" : "Offline"}</span>
      {isOnline ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
    </div>
  );
}
