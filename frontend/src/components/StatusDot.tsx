"use client";

import type { HealthResponse } from "@/lib/api";

interface StatusDotProps {
  health: HealthResponse | null;
  error: string | null;
}

/**
 * Compact status indicator for the header.
 * Replaces the large "Backend Status" card with a small colored dot.
 * Hover reveals version + environment in a tooltip.
 */
export function StatusDot({ health, error }: StatusDotProps) {
  const isHealthy = health && !error;
  const color = isHealthy ? "bg-green-500" : error ? "bg-red-500" : "bg-yellow-500";
  const label = isHealthy ? "Online" : error ? "Offline" : "Connecting";
  const tooltip = health
    ? `${label} · v${health.version} · ${health.environment}`
    : error
    ? `Offline · ${error}`
    : "Connecting to backend…";

  return (
    <div className="group relative flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        {isHealthy && (
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-60" />
        )}
        <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${color}`} />
      </span>
      <span className="text-xs text-slate-400 hidden sm:inline">{label}</span>

      {/* Tooltip on hover */}
      <div className="pointer-events-none absolute right-0 top-full z-10 mt-2 whitespace-nowrap rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 opacity-0 shadow-lg transition group-hover:opacity-100">
        {tooltip}
      </div>
    </div>
  );
}
