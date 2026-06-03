"use client";

/**
 * Animated gray placeholder block. Use while data is loading.
 * Combine multiple Skeletons to mimic the shape of the eventual content.
 */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />;
}

/**
 * Pre-built skeleton matching the shape of the "Run a Security Test" form
 * while scenarios are loading. Replaces the bare "Loading scenarios..." text.
 */
export function ScenarioFormSkeleton() {
  return (
    <div className="space-y-5 animate-fade-in" aria-busy="true" aria-label="Loading scenarios">
      {/* Scenario picker */}
      <div>
        <Skeleton className="h-3 w-24 mb-2" />
        <Skeleton className="h-9 w-full" />
      </div>
      {/* Techniques chips */}
      <div>
        <Skeleton className="h-3 w-32 mb-2" />
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-7 w-20" />
          ))}
        </div>
      </div>
      {/* Model selector */}
      <div>
        <Skeleton className="h-3 w-28 mb-2" />
        <Skeleton className="h-9 w-full" />
      </div>
      {/* Run button */}
      <Skeleton className="h-10 w-32" />
    </div>
  );
}
