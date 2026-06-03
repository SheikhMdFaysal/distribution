"use client";

import { useEffect, useRef, useState } from "react";
import { api, type DashboardAnalytics } from "@/lib/api";

interface StatsItem {
  label: string;
  value: number;
  suffix?: string;
  color: string;
  iconColor: string;
  Icon: () => React.ReactNode;
}

/**
 * Stats widget with animated counters.
 * Pulls real numbers from /api/v1/analytics/dashboard.
 * Numbers count up smoothly when they come into view.
 */
export function StatsWidget() {
  const [data, setData] = useState<DashboardAnalytics | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api
      .dashboardAnalytics()
      .then((d) => {
        setData(d);
        setLoaded(true);
      })
      .catch(() => {
        // Graceful degradation: show zeros instead of an error block
        setLoaded(true);
      });
  }, []);

  const stats: StatsItem[] = [
    {
      label: "Security tests run",
      value: data?.summary.total_tests ?? 0,
      color: "text-cyan-300",
      iconColor: "bg-cyan-500/10 text-cyan-300",
      Icon: ShieldIcon,
    },
    {
      label: "Vulnerabilities detected",
      value: data?.summary.total_vulnerabilities ?? 0,
      color: "text-rose-300",
      iconColor: "bg-rose-500/10 text-rose-300",
      Icon: BugIcon,
    },
    {
      label: "Vendors tested",
      value: data?.vendor_comparison.length ?? 0,
      color: "text-purple-300",
      iconColor: "bg-purple-500/10 text-purple-300",
      Icon: BuildingIcon,
    },
    {
      label: "Compliance frameworks",
      value: 6, // SOC 2, ISO 27001, GDPR, CCPA, NIST AI RMF, CPCSC
      color: "text-emerald-300",
      iconColor: "bg-emerald-500/10 text-emerald-300",
      Icon: ChecklistIcon,
    },
  ];

  return (
    <section className="mb-8 grid grid-cols-2 sm:grid-cols-4 gap-3 animate-fade-in">
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 transition"
        >
          <div className="flex items-center justify-between mb-2">
            <span className={`p-1.5 rounded-md ${s.iconColor}`}>
              <s.Icon />
            </span>
          </div>
          <div className={`text-2xl font-bold tabular-nums ${s.color}`}>
            <Counter value={s.value} active={loaded} />
            {s.suffix}
          </div>
          <div className="text-xs text-slate-500 mt-1">{s.label}</div>
        </div>
      ))}
    </section>
  );
}

/**
 * Counts up from 0 to the target value over ~1 second.
 * Re-counts whenever `value` changes.
 */
function Counter({ value, active }: { value: number; active: boolean }) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    const start = performance.now();
    const duration = 900;
    const from = 0;
    const to = value;

    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // Ease-out cubic for a smooth deceleration
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(from + (to - from) * eased));
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value, active]);

  return <>{display.toLocaleString()}</>;
}

// ---------- Icons (inline SVG, no extra dependency) ----------

function ShieldIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L4 6v6c0 5 3.5 9.5 8 10 4.5-.5 8-5 8-10V6l-8-4z" />
    </svg>
  );
}
function BugIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="8" y="6" width="8" height="14" rx="4" />
      <path d="M12 6V3M9 3l3 3 3-3M5 13H2M22 13h-3M5 8l3 2M19 8l-3 2M5 18l3-2M19 18l-3-2" />
    </svg>
  );
}
function BuildingIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="3" width="16" height="18" rx="1" />
      <path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M10 21v-4h4v4" />
    </svg>
  );
}
function ChecklistIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  );
}
