import { Cpu, Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative z-10 mt-12 border-t border-zinc-200 py-8 dark:border-white/[0.06]">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-[10px] text-zinc-500 dark:text-zinc-600 sm:flex-row sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-ember-600/80 dark:text-ember-300/70" />
          <span>
            GenAI Notebook Generator · FastAPI · nbformat · TensorFlow 2 / Keras
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono">
          <Cpu className="h-3.5 w-3.5 text-ember-600/80 dark:text-ember-300/60" />
          U1 templating · U2 LLM · U3 BLIP · U4 validation · U5 safety
        </div>
      </div>
    </footer>
  );
}
