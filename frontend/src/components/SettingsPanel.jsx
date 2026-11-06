import { Bot, Cpu, ShieldCheck, SlidersHorizontal } from "lucide-react";
import SectionHeading from "./SectionHeading.jsx";

const BATCH_OPTIONS = [16, 32, 64, 128];

export default function SettingsPanel({
  epochs,
  batchSize,
  useLlm,
  model,
  onEpochsChange,
  onBatchChange,
  onLlmChange,
}) {
  const maxEpochs = 30;
  const progress = ((Math.min(epochs, maxEpochs) - 1) / (maxEpochs - 1)) * 100;
  const runtime =
    model?.kind === "text"
      ? `≈ ${Math.max(2, Math.round(epochs * 0.8))}–${Math.max(4, Math.round(epochs * 1.4))} min on T4`
      : `≈ ${Math.max(1, Math.round(epochs * 0.6))}–${Math.max(3, Math.round(epochs * 1.2))} min on T4`;

  return (
    <section id="safety" className="glass-panel panel-padding">
      <SectionHeading
        index="03"
        title="Notebook settings"
        description="Tune the generated training config. Every value is written into the setup cell."
        icon={SlidersHorizontal}
      />

      <div className="grid gap-5 sm:grid-cols-2">
        <div className="rounded-2xl border border-zinc-200 bg-white dark:border-white/[0.06] dark:bg-white/[0.02] p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] font-medium text-zinc-600 dark:text-zinc-400">
              <Cpu className="h-3.5 w-3.5 text-ember-600 dark:text-ember-300" />
              Epochs
            </div>
            <span className="rounded-lg border border-ember-300/20 bg-ember-300/10 px-2 py-0.5 font-mono text-xs font-semibold text-ember-600 dark:text-ember-300">
              {epochs}
            </span>
          </div>
          <input
            type="range"
            min="1"
            max={maxEpochs}
            step="1"
            value={Math.min(epochs, maxEpochs)}
            onChange={(event) => onEpochsChange(Number(event.target.value))}
            className="range-input mt-4"
            style={{
              background: `linear-gradient(to right, #DA6556 0%, #DA6556 ${progress}%, var(--range-track) ${progress}%, var(--range-track) 100%)`,
            }}
            aria-label="Training epochs"
          />
          <div className="mt-2.5 flex items-center justify-between font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
            <span>1 · quick smoke</span>
            <span className="text-ember-600/80 dark:text-ember-300/70">{runtime}</span>
            <span>30 · quality</span>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-200 bg-white dark:border-white/[0.06] dark:bg-white/[0.02] p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] font-medium text-zinc-600 dark:text-zinc-400">
              <SlidersHorizontal className="h-3.5 w-3.5 text-ember-600 dark:text-ember-300" />
              Batch size
            </div>
            <span className="font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
              per step
            </span>
          </div>
          <div className="mt-3.5 grid grid-cols-4 gap-1.5">
            {BATCH_OPTIONS.map((option) => {
              const active = option === batchSize;
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => onBatchChange(option)}
                  className={`rounded-lg border py-2 font-mono text-[11px] font-medium transition ${
                    active
                      ? "border-ember-400/40 bg-ember-500/20 text-ember-600 dark:text-ember-300"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-ember-500/40 hover:text-ember-600 dark:border-white/[0.06] dark:bg-white/[0.02] dark:text-zinc-500 dark:hover:border-ember-400/20 dark:hover:text-zinc-200"
                  }`}
                >
                  {option}
                </button>
              );
            })}
          </div>
          <p className="mt-2.5 text-[10px] leading-relaxed text-zinc-500 dark:text-zinc-600">
            Larger batches stabilise losses but use more GPU memory.
          </p>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-4 rounded-2xl border border-zinc-200 bg-white dark:border-white/[0.06] dark:bg-white/[0.02] p-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-ember-300/20 bg-ember-300/10 text-ember-600 dark:text-ember-300">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <div className="text-[12px] font-medium text-zinc-800 dark:text-zinc-200">
              LLM code generation
            </div>
            <p className="mt-0.5 max-w-md text-[10.5px] leading-relaxed text-zinc-500">
              Uses Groq / OpenAI when configured, with automatic fallback to the
              vetted Keras templates. LLM cells pass the same safety gate.
            </p>
          </div>
        </div>

        <button
          type="button"
          role="switch"
          aria-checked={useLlm}
          aria-label="Toggle LLM code generation"
          onClick={() => onLlmChange(!useLlm)}
          className={`relative h-6 w-11 shrink-0 rounded-full border transition duration-300 ${
            useLlm
              ? "border-ember-300/30 bg-ember-gradient"
              : "border-zinc-300 bg-zinc-200 dark:border-white/10 dark:bg-white/10"
          }`}
        >
          <span
            className={`absolute top-0.5 h-[18px] w-[18px] rounded-full bg-white shadow-sm transition-transform duration-300 ${
              useLlm ? "translate-x-[22px]" : "translate-x-0.5"
            }`}
          />
        </button>
      </div>

      <div className="mt-3 flex items-start gap-2 px-1">
        <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400/80" />
        <p className="text-[10px] leading-relaxed text-zinc-500 dark:text-zinc-600">
          Safety gate: AST parsing, forbidden import/call scan, shell allow-list and
          TF2 compatibility checks run before packaging.
        </p>
      </div>
    </section>
  );
}
