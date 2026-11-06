import { Database, Sparkles } from "lucide-react";
import SectionHeading from "./SectionHeading.jsx";

export default function DatasetSelector({ datasets, selected, onSelect }) {
  return (
    <section id="datasets" className="glass-panel panel-padding">
      <SectionHeading
        index="02"
        title="Select a dataset"
        description="Only datasets compatible with the selected model are shown. License metadata is injected into cell one."
        icon={Database}
      />

      <div className="grid gap-3 sm:grid-cols-2">
        {datasets.map((dataset) => {
          const active = dataset.id === selected;
          return (
            <button
              key={dataset.id}
              type="button"
              onClick={() => onSelect(dataset)}
              aria-pressed={active}
              className={`relative overflow-hidden rounded-2xl border p-4 text-left transition duration-300 ${
                active
                  ? "border-ember-500/50 bg-ember-500/[0.08] shadow-glow-soft"
                  : "border-zinc-200 bg-white hover:border-ember-500/40 hover:bg-ember-50/60 dark:border-white/[0.07] dark:bg-white/[0.02] dark:hover:border-ember-400/30 dark:hover:bg-white/[0.04]"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        active ? "bg-ember-300 shadow-[0_0_10px_rgba(253,183,115,0.9)]" : "bg-zinc-300 dark:bg-zinc-600"
                      }`}
                    />
                    <span className="text-sm font-semibold text-zinc-900 dark:text-white">
                      {dataset.label}
                    </span>
                  </div>
                  <div className="mt-1 font-mono text-[10px] text-zinc-500">
                    {dataset.shape} · {dataset.samples}
                  </div>
                </div>
                {active ? (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ember-500">
                    <span className="h-1.5 w-1.5 rounded-full bg-white" />
                  </span>
                ) : null}
              </div>

              <p className="mt-2.5 line-clamp-2 text-[11px] leading-relaxed text-zinc-500">
                {dataset.description}
              </p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span
                  className={`inline-flex items-center rounded-full border px-2 py-1 text-[10px] font-medium ${
                    active
                      ? "border-ember-300/30 bg-ember-300/10 text-ember-600 dark:text-ember-300"
                      : "border-zinc-200 bg-zinc-100 text-zinc-500 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-zinc-400"
                  }`}
                >
                  {dataset.license.name}
                </span>
                <span className="truncate font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
                  {dataset.source}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-4 flex items-start gap-2 rounded-xl border border-zinc-200 bg-zinc-100/70 px-3 py-2.5 dark:border-white/[0.06] dark:bg-ink-900/60">
        <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ember-600 dark:text-ember-300" />
        <p className="text-[10.5px] leading-relaxed text-zinc-500">
          A license snapshot — name, attribution, URL and usage notes — is written to
          the first Markdown cell and exported beside the model weights.
        </p>
      </div>
    </section>
  );
}
