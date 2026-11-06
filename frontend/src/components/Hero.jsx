import { Check } from "lucide-react";

const pipeline = [
  "Environment setup",
  "Data loading",
  "Model architecture",
  "Training loop",
  "BLIP sanity check",
];

export default function Hero() {
  return (
    <section className="relative pt-16 sm:pt-24">
      <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
        <div className="animate-fade-up">
          <h1 className="max-w-3xl text-balance text-4xl font-semibold leading-[1.05] tracking-[-0.04em] text-zinc-900 dark:text-white sm:text-5xl lg:text-[3.4rem]">
            Ship runnable Colab notebooks for{" "}
            <span className="gradient-text">generative models</span>
          </h1>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <a href="#generator" className="btn-primary">
              Start building
            </a>
            <a href="#samples" className="btn-secondary">
              Inspect sample builds
            </a>
          </div>
        </div>

        <div className="relative animate-fade-up [animation-delay:120ms]">
          <div className="absolute -inset-6 -z-10 rounded-[2.5rem] bg-ember-500/10 blur-3xl" />
          <div className="glass-panel overflow-hidden">
            <div className="flex items-center gap-2.5 border-b border-zinc-200 px-5 py-4 dark:border-white/[0.06]">
              <span className="h-2.5 w-2.5 rounded-full bg-ember-600" />
              <span className="h-2.5 w-2.5 rounded-full bg-ember-400" />
              <span className="h-2.5 w-2.5 rounded-full bg-ember-300" />
            </div>

            <div className="mesh-lines px-5 py-6">
              <div className="mb-5 flex items-center gap-3">
                <div className="font-mono text-xs text-zinc-700 dark:text-zinc-200">
                  dcgan_fashion_mnist.ipynb
                </div>
              </div>

              <div className="space-y-2">
                {pipeline.map((step) => (
                  <div
                    key={step}
                    className="flex items-center justify-between gap-3 rounded-xl border border-zinc-200 bg-white px-4 py-3.5 dark:border-white/[0.05] dark:bg-ink-900/70"
                  >
                    <span className="truncate text-[12px] font-medium text-zinc-800 dark:text-zinc-200">
                      {step}
                    </span>
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ember-500/15 text-ember-600 dark:text-ember-300">
                      <Check className="h-3 w-3" />
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
