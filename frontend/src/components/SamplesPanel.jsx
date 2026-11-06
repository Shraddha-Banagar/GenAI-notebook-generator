import { Download, FileCode2, FlaskConical, Loader2 } from "lucide-react";
import { sampleUrl } from "../lib/api.js";

export default function SamplesPanel({ samples, loading }) {
  return (
    <section id="samples" className="glass-panel panel-padding">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="section-kicker">
            <FlaskConical className="h-3.5 w-3.5" />
            Reference builds
          </div>
          <h2 className="mt-1 text-sm font-semibold text-zinc-900 dark:text-white">
            Sample executions
          </h2>
        </div>
        <span className="chip">.ipynb</span>
      </div>

      <div className="mt-4 space-y-2.5">
        {loading ? (
          <div className="flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-4 text-[11px] text-zinc-500 dark:border-white/[0.06] dark:bg-white/[0.02]">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-ember-600 dark:text-ember-300" />
            Loading sample notebooks…
          </div>
        ) : samples?.length ? (
          samples.map((sample) => {
            const available = sample.available !== false;
            return (
              <a
                key={sample.id}
                href={available ? sampleUrl(sample.download_url) : undefined}
                download={sample.filename}
                aria-disabled={!available}
                className={`group flex items-start gap-3 rounded-xl border border-zinc-200 bg-white p-3 transition dark:border-white/[0.06] dark:bg-white/[0.02] ${
                  available
                    ? "hover:border-ember-500/40 hover:bg-ember-50/60 dark:hover:border-ember-400/30 dark:hover:bg-white/[0.04]"
                    : "cursor-not-allowed opacity-60"
                }`}
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-ember-300/20 bg-ember-300/10 text-ember-600 dark:border-ember-300/15 dark:text-ember-300">
                  <FileCode2 className="h-3.5 w-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-[11.5px] font-medium text-zinc-800 dark:text-zinc-200">
                      {sample.title}
                    </span>
                    <Download className="h-3.5 w-3.5 shrink-0 text-zinc-400 transition group-hover:text-ember-600 dark:text-zinc-600 dark:group-hover:text-ember-300" />
                  </div>
                  <p className="mt-0.5 line-clamp-2 text-[10px] leading-relaxed text-zinc-500">
                    {sample.description}
                  </p>
                  <div className="mt-1.5 flex items-center gap-2 font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
                    <span className="text-ember-600/80 dark:text-ember-300/70">
                      {sample.license}
                    </span>
                    <span className="h-1 w-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
                    <span>{available ? sample.filename : "not generated"}</span>
                  </div>
                </div>
              </a>
            );
          })
        ) : (
          <div className="rounded-xl border border-dashed border-zinc-300 bg-white/60 px-3 py-4 text-[10.5px] leading-relaxed text-zinc-500 dark:border-white/[0.08] dark:bg-white/[0.015]">
            Run{" "}
            <span className="font-mono text-ember-600/80 dark:text-ember-300/80">
              python backend/scripts/generate_samples.py
            </span>{" "}
            to create the reference notebooks.
          </div>
        )}
      </div>
    </section>
  );
}
