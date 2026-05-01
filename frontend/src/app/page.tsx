"use client";

import { useEffect, useState } from "react";
import {
  api,
  type AttackScenario,
  type HealthResponse,
  type TestRunDetails,
} from "@/lib/api";
import { getRemediation } from "@/lib/remediation";

// All free-tier models supported by the backend.
// (Backend's adapter factory routes "google", "groq", "openrouter", "huggingface".)
const FREE_MODELS = [
  { adapter: "google", model: "gemini-2.5-flash", vendor: "Google", label: "Gemini 2.5 Flash (Google)" },
  { adapter: "google", model: "gemini-2.0-flash", vendor: "Google", label: "Gemini 2.0 Flash (Google)" },
  { adapter: "groq", model: "llama-3.1-8b-instant", vendor: "Groq", label: "Llama 3.1 8B Instant (Groq)" },
  { adapter: "groq", model: "llama-3.3-70b-versatile", vendor: "Groq", label: "Llama 3.3 70B (Groq)" },
  { adapter: "openrouter", model: "inclusionai/ling-2.6-flash:free", vendor: "OpenRouter", label: "Ling 2.6 Flash — free (OpenRouter)" },
  { adapter: "openrouter", model: "tencent/hy3-preview:free", vendor: "OpenRouter", label: "Tencent HY3 Preview — free (OpenRouter)" },
];

const TECHNIQUES = ["poetry", "narrative", "metaphor", "euphemism", "role_shift"];

/** Random sample of N items from an array (no repeats). */
function randomSample<T>(arr: T[], n: number): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, Math.min(n, a.length));
}

const PROGRESS_STAGES = [
  "Generating stylistic variants",
  "Sending prompts to target model",
  "Analyzing model responses",
  "Computing CVSS risk scores",
  "Mapping to compliance frameworks",
];

export default function DashboardHome() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [scenarios, setScenarios] = useState<AttackScenario[]>([]);
  const [error, setError] = useState<string | null>(null);

  // form state
  const [scenarioId, setScenarioId] = useState<number | null>(null);
  const [techniques, setTechniques] = useState<string[]>(["poetry"]);
  const [modelIdx, setModelIdx] = useState(0);
  const [promptCount, setPromptCount] = useState(2);
  const [running, setRunning] = useState(false);
  const [progressStage, setProgressStage] = useState(0);
  const [result, setResult] = useState<TestRunDetails | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  // Custom prompt mode (Dr. Ray's feedback — "pick a card, any card")
  const [customPromptEnabled, setCustomPromptEnabled] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");

  // BYOM (Bring Your Own Model) state
  const [byomEnabled, setByomEnabled] = useState(false);
  const [byomUrl, setByomUrl] = useState("");
  const [byomKey, setByomKey] = useState("");
  const [byomModel, setByomModel] = useState("");
  const [byomVendor, setByomVendor] = useState("");

  // How-to-use panel
  const [showGuide, setShowGuide] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch((e: Error) => setError(e.message));
    api
      .listScenarios()
      .then((s) => {
        setScenarios(s);
        if (s.length) setScenarioId(s[0].id);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  // Cycle the progress stages while a test is running
  useEffect(() => {
    if (!running) return;
    setProgressStage(0);
    const interval = setInterval(() => {
      setProgressStage((s) => (s + 1) % PROGRESS_STAGES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [running]);

  const toggleTechnique = (t: string) => {
    setTechniques((cur) =>
      cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]
    );
  };

  const runTest = async () => {
    if (!scenarioId) return;
    const scenario = scenarios.find((s) => s.id === scenarioId);
    if (!scenario) return;

    setRunning(true);
    setRunError(null);
    setResult(null);

    try {
      // Build the target model: either BYOM (custom endpoint) or one of the preset free models
      let targetModel: Record<string, unknown>;
      if (byomEnabled) {
        if (!byomUrl || !byomModel) {
          throw new Error("BYOM requires endpoint URL and model name");
        }
        targetModel = {
          adapter: "custom",
          model: byomModel,
          vendor: byomVendor || "custom",
          type: "enterprise",
          base_url: byomUrl,
          api_key: byomKey,
        };
      } else {
        const m = FREE_MODELS[modelIdx];
        targetModel = { adapter: m.adapter, model: m.model, vendor: m.vendor, type: "enterprise" };
      }

      // Build the baseline prompts: either user's custom prompt OR random sample from library
      let prompts: string[];
      if (customPromptEnabled) {
        const trimmed = customPrompt.trim();
        if (!trimmed) {
          throw new Error("Please type a prompt or switch back to the preset library.");
        }
        prompts = [trimmed];
      } else {
        prompts = randomSample(scenario.default_prompts, promptCount);
      }

      const created = await api.runTest({
        test_name: `Live demo: ${scenario.name} - ${new Date().toISOString()}`,
        description: customPromptEnabled ? "Custom user prompt" : "Random sample from preset library",
        attack_scenario_id: scenarioId,
        baseline_prompts: prompts,
        techniques,
        target_models: [targetModel as never],
        variants_per_technique: 1,
      });
      const details = await api.getTest(created.test_id);
      setResult(details);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  const apiBase =
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
              Enterprise AI Security Red Teaming Platform
            </h1>
            <p className="mt-2 text-slate-400">
              Stress-test AI models for security vulnerabilities and compliance risks.
            </p>
          </div>
          <button
            onClick={() => setShowGuide((v) => !v)}
            className="text-xs px-3 py-1.5 rounded border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 transition shrink-0"
          >
            {showGuide ? "✕ Close guide" : "?  How to use"}
          </button>
        </header>

        {/* Collapsible How-to-use panel */}
        {showGuide && (
          <section className="mb-8 rounded-xl bg-slate-900 border border-cyan-500/30 p-6">
            <h2 className="text-lg font-semibold mb-3 text-cyan-300">How to use this platform</h2>
            <ol className="list-decimal list-inside space-y-2 text-sm text-slate-300">
              <li>
                <strong>Pick an attack scenario.</strong> Each scenario tests a specific
                vendor promise (e.g., &quot;your data is isolated&quot;) using a curated
                library of baseline prompts.
              </li>
              <li>
                <strong>Choose stylistic techniques.</strong> Each baseline prompt gets
                rewritten as poetry, narrative, metaphor, etc. — to bypass simple keyword
                filters and probe for deeper vulnerabilities.
              </li>
              <li>
                <strong>Pick a target AI model.</strong> Choose from preset free-tier
                models (Gemini, Groq Llama, OpenRouter) or enable{" "}
                <em className="text-cyan-300">Bring Your Own Model</em> to test your
                organization&apos;s own AI deployment via its OpenAI-compatible endpoint.
              </li>
              <li>
                <strong>Choose your prompt source.</strong> Either let the platform sample
                random prompts from the curated scenario library (slider 1–5), or toggle{" "}
                <em className="text-cyan-300">&quot;Use my own prompt&quot;</em> and type
                anything you want to test. Your custom prompt will be transformed by every
                selected technique and scored independently.
              </li>
              <li>
                <strong>Run the test.</strong> Watch the live progress as the platform
                generates variants, sends them to the model, scores responses on a 0–10
                CVSS scale, and maps findings to compliance frameworks (SOC 2, ISO 27001,
                GDPR, NIST AI RMF, CCPA, CPCSC).
              </li>
              <li>
                <strong>Review results.</strong> See per-variant breakdown — original
                prompt, rewritten variant, model response, leakage detection, risk score.
                Download the JSON report or print it as PDF.
              </li>
            </ol>
            <p className="mt-4 text-xs text-slate-500">
              <strong>Privacy note:</strong> BYOM credentials are sent to the backend
              over HTTPS for the duration of the test only. Keys are not stored, logged,
              or persisted. For production use, deploy a private instance.
            </p>
          </section>
        )}

        {/* Backend status */}
        <section className="mb-8 rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-3">Backend Status</h2>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          {health && (
            <div className="grid grid-cols-3 gap-4">
              <Stat label="Status" value={health.status} color="green" />
              <Stat label="Version" value={health.version} color="cyan" />
              <Stat label="Environment" value={health.environment} color="purple" />
            </div>
          )}
        </section>

        {/* Run a test */}
        <section className="mb-8 rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-4">Run a Security Test</h2>

          {scenarios.length === 0 && <p className="text-slate-400">Loading scenarios...</p>}

          {scenarios.length > 0 && (
            <div className="space-y-5">
              {/* Scenario picker */}
              <div>
                <label className="block text-xs uppercase tracking-wide text-slate-500 mb-2">
                  Attack scenario
                </label>
                <select
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                  value={scenarioId ?? ""}
                  onChange={(e) => setScenarioId(Number(e.target.value))}
                  disabled={running}
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                {scenarioId && (
                  <p className="mt-2 text-xs text-slate-500">
                    {scenarios.find((s) => s.id === scenarioId)?.description}
                  </p>
                )}
              </div>

              {/* Techniques */}
              <div>
                <label className="block text-xs uppercase tracking-wide text-slate-500 mb-2">
                  Stylistic transformation techniques
                </label>
                <div className="flex flex-wrap gap-2">
                  {TECHNIQUES.map((t) => (
                    <button
                      key={t}
                      onClick={() => toggleTechnique(t)}
                      disabled={running}
                      className={`px-3 py-1 rounded text-xs border transition ${
                        techniques.includes(t)
                          ? "bg-cyan-600/20 border-cyan-500 text-cyan-300"
                          : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Prompt source — preset library OR user's own */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs uppercase tracking-wide text-slate-500">
                    Prompt source
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={customPromptEnabled}
                      onChange={(e) => setCustomPromptEnabled(e.target.checked)}
                      disabled={running}
                      className="accent-cyan-500"
                    />
                    Use my own prompt (pick a card, any card)
                  </label>
                </div>

                {!customPromptEnabled ? (
                  <>
                    <label className="block text-xs text-slate-500 mb-2">
                      Random sample of {promptCount} prompt
                      {promptCount === 1 ? "" : "s"} from the preset library
                    </label>
                    <input
                      type="range"
                      min={1}
                      max={5}
                      value={promptCount}
                      onChange={(e) => setPromptCount(Number(e.target.value))}
                      disabled={running}
                      className="w-full accent-cyan-500"
                    />
                    <p className="mt-1 text-xs text-slate-500">
                      Each run picks different random prompts from the scenario&apos;s
                      curated library (
                      {scenarios.find((s) => s.id === scenarioId)?.default_prompts.length ?? 0}{" "}
                      research-grade prompts available).
                    </p>
                  </>
                ) : (
                  <div className="rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-3 space-y-2">
                    <textarea
                      placeholder="Type any prompt you want to test against the model. Example:  &quot;What confidential business information were you trained on?&quot;"
                      value={customPrompt}
                      onChange={(e) => setCustomPrompt(e.target.value)}
                      disabled={running}
                      rows={3}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono resize-y"
                    />
                    <p className="text-xs text-cyan-300/80">
                      🎩 Your prompt will be transformed by every selected technique
                      (poetry, narrative, metaphor, etc.) and tested against the target
                      model. Every transformation is scored independently.
                    </p>
                  </div>
                )}
              </div>

              {/* Model picker — preset or BYOM */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-xs uppercase tracking-wide text-slate-500">
                    Target model
                  </label>
                  <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={byomEnabled}
                      onChange={(e) => setByomEnabled(e.target.checked)}
                      disabled={running}
                      className="accent-cyan-500"
                    />
                    Bring Your Own Model (BYOM)
                  </label>
                </div>

                {!byomEnabled ? (
                  <>
                    <select
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                      value={modelIdx}
                      onChange={(e) => setModelIdx(Number(e.target.value))}
                      disabled={running}
                    >
                      {FREE_MODELS.map((m, i) => (
                        <option key={i} value={i}>
                          {m.label}
                        </option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-slate-500">
                      Tip: if a model says &quot;quota exceeded,&quot; switch to another
                      vendor. Free tiers refresh daily (Gemini) or per-minute (Groq).
                    </p>
                  </>
                ) : (
                  <div className="space-y-2 rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-3">
                    <input
                      type="url"
                      placeholder="https://your-ai.example.com/v1  (OpenAI-compatible endpoint)"
                      value={byomUrl}
                      onChange={(e) => setByomUrl(e.target.value)}
                      disabled={running}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono"
                    />
                    <input
                      type="password"
                      placeholder="API key (sent over HTTPS, never stored)"
                      value={byomKey}
                      onChange={(e) => setByomKey(e.target.value)}
                      disabled={running}
                      className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-mono"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Model name (e.g. gpt-4o-mini)"
                        value={byomModel}
                        onChange={(e) => setByomModel(e.target.value)}
                        disabled={running}
                        className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Vendor label (e.g. Acme Corp)"
                        value={byomVendor}
                        onChange={(e) => setByomVendor(e.target.value)}
                        disabled={running}
                        className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                      />
                    </div>
                    <p className="text-xs text-cyan-300/70">
                      🔒 Your endpoint must be OpenAI-compatible
                      (<code>/v1/chat/completions</code> format). Keys are forwarded to your
                      endpoint for this run only — never logged or persisted.
                    </p>
                  </div>
                )}
              </div>

              {/* Run button */}
              <button
                onClick={runTest}
                disabled={running || !techniques.length}
                className="w-full py-3 rounded-lg font-semibold transition bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {running ? "Running test..." : "▶  Run security test"}
              </button>
              {runError && (
                <p className="text-red-400 text-sm">Error: {runError}</p>
              )}

              {/* Animated progress */}
              {running && <ProgressBar stageIdx={progressStage} />}
            </div>
          )}
        </section>

        {/* Result */}
        {result && (
          <ResultPanel result={result} apiBase={apiBase} scenarios={scenarios} />
        )}
      </div>
    </main>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: "green" | "cyan" | "purple" }) {
  const colorMap = { green: "text-green-400", cyan: "text-cyan-400", purple: "text-purple-400" };
  return (
    <div className="rounded-lg bg-slate-800/50 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${colorMap[color]}`}>{value}</div>
    </div>
  );
}

function ProgressBar({ stageIdx }: { stageIdx: number }) {
  return (
    <div className="rounded-lg bg-slate-800/30 border border-slate-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-sm text-cyan-300">{PROGRESS_STAGES[stageIdx]}…</span>
        </div>
        <span className="text-xs text-slate-500">
          {stageIdx + 1} of {PROGRESS_STAGES.length}
        </span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 transition-all duration-700 ease-out"
          style={{ width: `${((stageIdx + 1) / PROGRESS_STAGES.length) * 100}%` }}
        />
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {PROGRESS_STAGES.map((s, i) => (
          <span
            key={s}
            className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded ${
              i < stageIdx
                ? "text-slate-500"
                : i === stageIdx
                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                : "text-slate-600"
            }`}
          >
            {s.split(" ")[0]}
          </span>
        ))}
      </div>
    </div>
  );
}

function isQuotaError(text: string) {
  if (!text) return false;
  const t = text.toLowerCase();
  return (
    t.includes("quota") ||
    t.includes("rate limit") ||
    t.includes("429") ||
    t.includes("exceeded")
  );
}

function ResultPanel({
  result,
  apiBase,
  scenarios,
}: {
  result: TestRunDetails;
  apiBase: string;
  scenarios: AttackScenario[];
}) {
  const riskColor =
    result.risk_level === "HIGH"
      ? "text-red-400"
      : result.risk_level === "MEDIUM"
      ? "text-amber-400"
      : "text-green-400";

  const exportJsonUrl = `${apiBase}/api/v1/security-tests/${result.id}/export`;

  // Look up the scenario slug ("enterprise_data_isolation") for remediation guidance
  const matchedScenario = scenarios.find((s) => s.id === result.attack_scenario.id);
  const scenarioKey = matchedScenario?.scenario_id ?? "default";

  // Did any model run report leakage?
  const hasVulnerability = result.baseline_prompts.some((bp) =>
    bp.variants.some((v) => v.model_runs.some((r) => r.evaluation?.leakage_detected))
  );

  return (
    <section className="rounded-xl bg-slate-900 border border-slate-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Test Result</h2>
        <div className="flex gap-2">
          <a
            href={exportJsonUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs px-3 py-1.5 rounded border border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 transition"
          >
            ⬇ Download report (JSON)
          </a>
          <button
            onClick={() => window.print()}
            className="text-xs px-3 py-1.5 rounded border border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
          >
            🖨 Print
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Metric label="Total runs" value={String(result.total_runs)} />
        <Metric
          label="Vulnerabilities"
          value={String(result.vulnerabilities_found)}
          color={result.vulnerabilities_found > 0 ? "text-red-400" : "text-green-400"}
        />
        <Metric
          label="Avg risk score"
          value={result.avg_risk_score?.toFixed(1) ?? "—"}
          color={riskColor}
        />
        <Metric label="Risk level" value={result.risk_level ?? "—"} color={riskColor} />
      </div>

      {hasVulnerability && (
        <RemediationPanel scenarioKey={scenarioKey} />
      )}

      <div className="space-y-3">
        {result.baseline_prompts.map((bp) =>
          bp.variants.map((v) => (
            <div key={v.id} className="rounded-lg bg-slate-800/50 p-4 border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs uppercase tracking-wide bg-cyan-600/30 text-cyan-300 px-2 py-0.5 rounded">
                  {v.technique}
                </span>
                <span className="text-xs text-slate-500">Original: {bp.prompt_text}</span>
              </div>
              <p className="text-sm text-slate-300 italic mb-2 whitespace-pre-line">
                Variant: {v.variant_text}
              </p>
              {v.model_runs.map((mr) => (
                <div key={mr.id} className="mt-2 pt-2 border-t border-slate-700">
                  <div className="text-xs text-slate-500 mb-1">
                    Model response from {mr.model_name}:
                  </div>
                  {(() => {
                    const text = (mr.response_text || "").trim();
                    if (mr.error_message) {
                      return (
                        <div className="rounded bg-red-500/10 border border-red-500/30 p-3 text-sm text-red-200">
                          ⛔ <strong>Model error:</strong> {mr.error_message}
                        </div>
                      );
                    }
                    if (isQuotaError(text)) {
                      return (
                        <div className="rounded bg-amber-500/10 border border-amber-500/30 p-3 text-sm text-amber-200">
                          ⚠ <strong>Free-tier quota exhausted</strong> for{" "}
                          <code className="bg-amber-900/40 px-1.5 py-0.5 rounded">
                            {mr.model_name}
                          </code>
                          .
                          <br />
                          <span className="text-xs text-amber-300/80 mt-1 block">
                            Pick a different model from the dropdown above (Groq and
                            OpenRouter have separate quotas) or wait until tomorrow when
                            Gemini resets. This is not a platform error — the AI provider
                            rejected the request.
                          </span>
                        </div>
                      );
                    }
                    if (!text) {
                      return (
                        <div className="rounded bg-slate-800 border border-slate-600 p-3 text-sm text-slate-300">
                          🤐 <strong>Empty response</strong> — the model returned no
                          content for this variant.
                          <br />
                          <span className="text-xs text-slate-400 mt-1 block">
                            This usually means: (1) the model silently refused (some free
                            models output nothing instead of a refusal message), (2) free-tier
                            burst rate limiting, or (3) the model&apos;s internal safety filter
                            blocked the response. Try a different model from the dropdown,
                            slow down requests, or rerun the test.
                          </span>
                        </div>
                      );
                    }
                    return (
                      <p className="text-sm text-slate-300 mb-2 whitespace-pre-line">
                        {text}
                      </p>
                    );
                  })()}
                  {mr.evaluation && (
                    <div className="flex gap-3 text-xs mt-2">
                      <span
                        className={
                          mr.evaluation.leakage_detected
                            ? "text-red-400"
                            : "text-green-400"
                        }
                      >
                        {mr.evaluation.leakage_detected ? "⚠ Leakage detected" : "✓ No leakage"}
                      </span>
                      <span className="text-slate-400">
                        Risk: {mr.evaluation.risk_score.toFixed(1)} ({mr.evaluation.risk_level})
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      <p className="mt-4 text-xs text-slate-600">
        Report ID: {result.id} · Generated{" "}
        {result.completed_at ? new Date(result.completed_at).toLocaleString() : "—"}
      </p>
    </section>
  );
}

function Metric({
  label,
  value,
  color = "text-cyan-400",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="rounded-lg bg-slate-800/50 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-lg font-bold ${color}`}>{value}</div>
    </div>
  );
}

function RemediationPanel({ scenarioKey }: { scenarioKey: string }) {
  const r = getRemediation(scenarioKey);
  return (
    <div className="rounded-xl border border-amber-500/40 bg-amber-500/5 p-5 mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-amber-400 text-xl">⚠</span>
        <h3 className="text-base font-semibold text-amber-200">
          Recommended Remediation
        </h3>
      </div>

      <div className="space-y-4 text-sm">
        <div>
          <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
            What happened
          </div>
          <p className="text-slate-300">{r.whatHappened}</p>
        </div>

        <div>
          <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
            Why it matters
          </div>
          <p className="text-slate-300">{r.whyItMatters}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
              Immediate actions
            </div>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm">
              {r.immediateActions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
              Long-term fixes
            </div>
            <ul className="list-disc list-inside space-y-1 text-slate-300 text-sm">
              {r.longTermFixes.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
              Compliance impact
            </div>
            <ul className="space-y-1 text-slate-300 text-xs">
              {r.complianceImpact.map((c, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-400 mt-0.5">●</span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="text-xs uppercase tracking-wide text-amber-300/80 mb-1">
              Who to notify
            </div>
            <ul className="space-y-1 text-slate-300 text-xs">
              {r.whoToNotify.map((w, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-0.5">●</span>
                  <span>{w}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
