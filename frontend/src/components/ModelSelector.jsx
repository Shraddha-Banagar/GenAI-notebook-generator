import { Sparkles } from "lucide-react";
import SectionHeading from "./SectionHeading.jsx";

export default function ModelSelector({ models, selected, onSelect }) {
  return (
    <section className="glass-panel panel-padding">
      <SectionHeading
        index="01"
        title="Choose a model"
        description="Three production-shaped reference implementations, each with its own training strategy."
        icon={Sparkles}
      />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {models.map((model) => {
          const active = model.id === selected;
          return (
            <button
              key={model.id}
              type="button"
              onClick={() => onSelect(model)}
              aria-pressed={active}
              className={`group relative flex flex-col rounded-2xl border p-4 text-left transition duration-300 ${
                active
                  ? "border-ember-500/60 bg-gradient-to-b from-ember-600/[0.18] to-ember-500/[0.04] shadow-glow"
                  : "border-zinc-200 bg-white hover:-translate-y-0.5 hover:border-ember-500/40 hover:bg-ember-50/60 dark:border-white/[0.07] dark:bg-white/[0.02] dark:hover:border-ember-500/30 dark:hover:bg-white/[0.04]"
              }`}
            >
              {active ? (
                <span className="absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-ember-300 to-transparent" />
              ) : null}

              <div className="flex items-start justify-end">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full border transition ${
                    active
                      ? "border-ember-300/40 bg-ember-500"
                      : "border-zinc-300 bg-transparent dark:border-white/10"
                  }`}
                >
                  {active ? (
                    <span className="h-1.5 w-1.5 rounded-full bg-white" />
                  ) : null}
                </span>
              </div>

              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-white">
                  {model.label}
                </span>
                <span className="rounded-full border border-zinc-200 bg-zinc-100 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wide text-zinc-500 dark:border-white/[0.08] dark:bg-white/[0.03]">
                  {model.family}
                </span>
              </div>
              <p className="mt-1.5 line-clamp-3 text-[11px] leading-relaxed text-zinc-500">
                {model.description}
              </p>

              <div className="mt-3 flex flex-wrap gap-1">
                {model.highlights.slice(0, 2).map((highlight) => (
                  <span
                    key={highlight}
                    className="rounded-md bg-zinc-100 px-1.5 py-0.5 text-[9px] text-zinc-500 dark:bg-white/[0.04]"
                  >
                    {highlight}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
