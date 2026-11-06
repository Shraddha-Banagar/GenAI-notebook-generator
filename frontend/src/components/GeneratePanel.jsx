import { AlertCircle, ShieldCheck } from "lucide-react";

export default function GeneratePanel({
  onGenerate,
  status,
  error,
  progressLabel,
  summary,
}) {
  const loading = status === "generating";
  const success = status === "success";
  const hasError = Boolean(error);

  return (
    <section className="glass-panel panel-padding">
      <div className="flex items-center justify-between gap-3">
        <div className="section-kicker">
          <span className="flex h-5 w-5 items-center justify-center rounded-md border border-ember-300/20 bg-ember-300/10 text-[10px] text-ember-300">
            04
          </span>
          <span>Build notebook</span>
        </div>
        {summary ? (
          <span className="hidden items-center gap-1.5 font-mono text-[10px] text-zinc-500 sm:flex dark:text-zinc-600">
            {summary}
            <span className="h-1 w-1 rounded-full bg-ember-500" />
            nbformat 4.5
          </span>
        ) : null}
      </div>

      <button
        type="button"
        onClick={onGenerate}
        disabled={loading}
        className="btn-primary mt-4 w-full text-[13px]"
      >
        {loading
          ? "Composing notebook"
          : success
            ? "Regenerate notebook"
            : "Generate Colab notebook"}
      </button>

      {loading ? (
        <div className="mt-4">
          <div className="relative h-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-white/[0.06]">
            <div className="absolute inset-y-0 w-1/3 animate-scan-line rounded-full bg-ember-gradient" />
          </div>
          <div className="mt-2.5 flex items-center justify-between text-[10px] text-zinc-500">
            <span>{progressLabel}</span>
            <span className="font-mono text-ember-600/80 dark:text-ember-300/70">
              packaging…
            </span>
          </div>
        </div>
      ) : (
        <div className="mt-3 flex items-center justify-between gap-3 px-0.5">
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 dark:text-zinc-600">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500/80 dark:text-emerald-400/70" />
            Syntax · safety · TF2 · license checks included
          </div>
          <span className="font-mono text-[9px] text-zinc-400 dark:text-zinc-700">
            U1 → U5
          </span>
        </div>
      )}

      {hasError ? (
        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-ember-500/25 bg-ember-500/[0.08] px-3 py-2.5">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-ember-400" />
          <div>
            <div className="text-[11px] font-semibold text-ember-600 dark:text-ember-300">
              Generation failed
            </div>
            <p className="mt-0.5 text-[10.5px] leading-relaxed text-ember-600/80 dark:text-ember-200/70">
              {error}
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
