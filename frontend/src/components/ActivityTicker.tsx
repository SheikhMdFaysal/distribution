"use client";

import { useEffect, useState } from "react";
import { api, type ActivityEntry } from "@/lib/api";

/**
 * Scrolling ticker of recent anonymized test activity.
 * Refreshes every 30 seconds. Hidden when there is no activity yet.
 */
export function ActivityTicker() {
  const [items, setItems] = useState<ActivityEntry[]>([]);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .recentActivity(15)
        .then((r) => {
          if (!cancelled) {
            setItems(r.activity);
            setFailed(false);
          }
        })
        .catch(() => {
          if (!cancelled) setFailed(true);
        });
    };
    load();
    // Poll every 60s (was 30s) to reduce database connection pressure.
    const id = window.setInterval(load, 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  if (failed || items.length === 0) {
    return null; // Quietly hide on empty/failed states; no clutter
  }

  // Duplicate items once so the CSS ticker animation can loop seamlessly
  const looped = [...items, ...items];

  return (
    <div
      className="mb-6 rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden"
      aria-label="Recent platform activity"
    >
      <div className="flex items-stretch">
        <div className="flex items-center gap-2 px-3 py-2 border-r border-slate-800 bg-slate-950 shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
            Live
          </span>
        </div>
        <div className="relative flex-1 overflow-hidden">
          <div className="flex gap-6 animate-ticker whitespace-nowrap py-2 px-4">
            {looped.map((item, idx) => (
              <ActivityPill key={`${item.run_id}-${idx}`} item={item} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ActivityPill({ item }: { item: ActivityEntry }) {
  const verb = item.leakage_detected ? "detected vulnerability on" : "passed test on";
  const color = item.leakage_detected ? "text-rose-300" : "text-emerald-300";
  const time = item.timestamp ? formatRelativeTime(item.timestamp) : "just now";

  return (
    <span className="text-xs text-slate-400 inline-flex items-center gap-2 shrink-0">
      <span className="font-mono text-slate-500">#{item.run_id}</span>
      <span className={color}>{verb}</span>
      <span className="text-slate-200">{item.model}</span>
      <span className="text-slate-500">({item.vendor})</span>
      <span className="text-slate-600">·</span>
      <span className="text-slate-500">{time}</span>
    </span>
  );
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
