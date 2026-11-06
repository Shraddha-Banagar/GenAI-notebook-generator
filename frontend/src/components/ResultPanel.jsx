import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Code2,
  FileCode2,
  FileText,
  Layers,
  Loader2,
  Scale,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { downloadNotebook } from "../lib/api.js";
import ValidationChecks from "./ValidationChecks.jsx";

const TABS = [
  { id: "notebook", label: "Notebook" },
  { id: "checks", label: "Checks" },
  { id: "license", label: "License" },
];

function sourceOf(cell) {
  const source = cell?.source ?? "";
  return Array.isArray(source) ? source.join("") : String(source);
}

function CellCard({ cell, index }) {
  const [expanded, setExpanded] = useState(false);
  const source = sourceOf(cell).trim();
  const section = cell?.metadata?.genai_section ?? "cell";
  const fromLlm = Boolean(cell?.metadata?.genai_llm_generated);
  const isCode = cell?.cell_type === "code";
  const canExpand = source.split("\n").length > 7 || source.length > 480;
  const display = expanded || !canExpand ? source : source.split("\n").slice(0, 7).join("\n");

  return (
    <div
      className={`rounded-xl border bg-white dark:bg-ink-900/60 ${
        index === 0
          ? "border-ember-500/20 dark:border-ember-300/20"
          : "border-zinc-200 dark:border-white/[0.06]"
      }`}
    >
      <div className="flex items-center justify-between gap-2 border-b border-zinc-200 px-3 py-2 dark:border-white/[0.04]">
        <div className="flex min-w-0 items-center gap-2">
          <span className="font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
            {String(index + 1).padStart(2, "0")}
          </span>
          <span
            className={`rounded-md px-1.5 py-0.5 font-mono text-[8px] font-semibold uppercase tracking-wide ${
              isCode
                ? "bg-ember-500/15 text-ember-600 dark:text-ember-300"
                : "bg-zinc-100 text-zinc-500 dark:bg-white/[0.05] dark:text-zinc-400"
            }`}
          >
            {isCode ? "code" : "md"}
          </span>
          <span className="truncate text-[10px] text-zinc-500">{section}</span>
        </div>
        <div className="flex items-center gap-1.5">
          {fromLlm ? (
            <span className="rounded-md border border-ember-300/20 bg-ember-300/10 px-1.5 py-0.5 text-[8px] font-medium text-ember-600 dark:text-ember-300">
              LLM
            </span>
          ) : null}
          <Code2 className="h-3 w-3 text-zinc-400 dark:text-zinc-700" />
        </div>
      </div>
      <div className="px-3 py-2.5">
        <pre className="code-source">{display || "—"}</pre>
        {canExpand ? (
          <button
            type="button"
            onClick={() => setExpanded((value) => !value)}
            className="mt-1.5 inline-flex items-center text-[9px] font-medium text-ember-600/80 transition hover:text-ember-600 hover:opacity-90 dark:text-ember-300/80 dark:hover:text-ember-300"
          >
            {expanded ? "Collapse" : "Expand cell"}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function FindingList({ findings, tone }) {
  if (!findings?.length) return null;
  return (
    <div className="mt-4 space-y-2">
      {findings.map((finding, index) => (
        <div
          key={`${finding.code}-${index}`}
          className={`flex items-start gap-2 rounded-xl border px-3 py-2 ${
            tone === "error"
              ? "border-ember-500/25 bg-ember-500/[0.07]"
              : "border-ember-300/20 bg-ember-300/[0.05]"
          }`}
        >
          <AlertTriangle
            className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${
              tone === "error" ? "text-ember-400" : "text-ember-300"
            }`}
          />
          <div>
            <div className="font-mono text-[9px] uppercase tracking-wide text-zinc-500">
              {finding.code}
              {finding.cell_index != null ? ` · cell ${finding.cell_index}` : ""}
            </div>
            <p className="mt-0.5 text-[10.5px] leading-relaxed text-zinc-600 dark:text-zinc-400">
              {finding.message}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ResultPanel({ result, status }) {
  const [tab, setTab] = useState("notebook");
  const loading = status === "generating";

  useEffect(() => {
    setTab("notebook");
  }, [result?.filename, result?.generation?.duration_ms]);

  if (loading) {
    return (
      <section className="glass-panel panel-padding min-h-[540px]">
        <div className="flex items-center gap-3">
          <div className="icon-tile">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
          <div>
            <div className="text-sm font-semibold text-zinc-900 dark:text-white">
              Assembling notebook
            </div>
            <div className="text-[10px] text-zinc-500">
              templating · LLM hand-off · validation
            </div>
          </div>
        </div>
        <div className="mt-6 space-y-3">
          {[72, 50, 88, 62, 80, 45].map((width, index) => (
            <div
              key={index}
              className="h-3 animate-pulse rounded-full bg-zinc-200 dark:bg-white/[0.05]"
              style={{ width: `${width}%`, animationDelay: `${index * 90}ms` }}
            />
          ))}
        </div>
        <div className="mt-8 rounded-2xl border border-dashed border-zinc-300 bg-white/60 p-5 dark:border-white/[0.08] dark:bg-white/[0.015]">
          <div className="flex items-center gap-2 text-[11px] text-zinc-500">
            <ShieldCheck className="h-4 w-4 text-ember-600 dark:text-ember-300" />
            Running final safety + TF2 checks…
          </div>
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="glass-panel panel-padding min-h-[540px]">
        <div className="flex items-center justify-between">
          <div>
            <div className="section-kicker">Live preview</div>
            <h2 className="section-title">Your notebook lands here</h2>
          </div>
          <span className="chip">
            <Clock3 className="h-3 w-3" />
            waiting
          </span>
        </div>

        <div className="mt-5 flex min-h-[390px] flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-300 bg-white/60 px-6 py-10 text-center dark:border-white/[0.08] dark:bg-white/[0.015]">
          <div className="relative">
            <div className="absolute -inset-5 rounded-full bg-ember-500/15 blur-2xl" />
            <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl border border-ember-300/20 bg-gradient-to-br from-ember-600/30 to-ember-500/5 text-ember-600 dark:text-ember-300">
              <FileCode2 className="h-6 w-6" />
            </div>
          </div>
          <h3 className="mt-5 text-sm font-semibold text-zinc-900 dark:text-white">
            Pick a model and press generate
          </h3>
          <p className="mt-1.5 max-w-xs text-[11px] leading-relaxed text-zinc-500">
            You will get a downloadable `.ipynb`, a cell-by-cell preview, and a
            complete validation report.
          </p>

          <div className="mt-6 w-full max-w-sm space-y-2 text-left">
            {[
              { icon: Scale, label: "Dataset license cell", hint: "cell 01" },
              { icon: Layers, label: "Training + inference sections", hint: "U1" },
              { icon: Sparkles, label: "BLIP caption sanity check", hint: "U3" },
              { icon: ShieldCheck, label: "AST + TF2 safety report", hint: "U4 / U5" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center gap-2.5 rounded-xl border border-zinc-200 bg-white px-3 py-2 dark:border-white/[0.05] dark:bg-ink-900/50"
                >
                  <Icon className="h-3.5 w-3.5 text-ember-600/80 dark:text-ember-300/70" />
                  <span className="flex-1 text-[10.5px] text-zinc-600 dark:text-zinc-400">
                    {item.label}
                  </span>
                  <span className="font-mono text-[8px] text-zinc-400 dark:text-zinc-700">
                    {item.hint}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    );
  }

  const cells = result.notebook?.cells ?? [];
  const codeCells = cells.filter((cell) => cell.cell_type === "code").length;
  const validation = result.validation ?? {};
  const generation = result.generation ?? {};
  const meta = result.meta ?? {};
  const license = meta.license ?? {};
  const passed = Boolean(validation.passed);
  const hasWarnings = (validation.warnings ?? []).length > 0;

  return (
    <section className="glass-panel animate-fade-in overflow-hidden border-ember-500/50 bg-gradient-to-br from-ember-300/20 via-ember-400/10 to-ember-500/[0.06] ring-1 ring-ember-500/25 shadow-[0_0_0_1px_rgba(218,101,86,0.18),0_30px_70px_-30px_rgba(161,70,70,0.5)]">
      <div className="border-b border-zinc-200 p-5 dark:border-white/[0.06]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <div className="icon-tile h-10 w-10 shrink-0 rounded-xl">
              <FileCode2 className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <div className="truncate font-mono text-[12px] font-medium text-zinc-900 dark:text-white">
                {result.filename}
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-zinc-500">
                <span>{meta.model_label}</span>
                <span className="text-zinc-300 dark:text-zinc-700">/</span>
                <span>{meta.dataset_label}</span>
                <span className="text-zinc-300 dark:text-zinc-700">/</span>
                <span>{generation.duration_ms ?? "—"} ms</span>
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={() => downloadNotebook(result.notebook, result.filename)}
            className="btn-primary shrink-0 text-[11px]"
          >
            Download
          </button>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="chip">
            <FileText className="h-3 w-3" />
            {cells.length} cells
          </span>
          <span className="chip">
            <Code2 className="h-3 w-3" />
            {codeCells} code
          </span>
          <span className="chip">
            <Sparkles className="h-3 w-3" />
            {generation.source === "llm" ? "LLM-assisted" : "Template"}
          </span>
          <span
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-medium ${
              passed
                ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-700 dark:border-emerald-400/20 dark:text-emerald-300"
                : "border-ember-500/25 bg-ember-500/10 text-ember-600 dark:text-ember-300"
            }`}
          >
            {passed ? (
              <CheckCircle2 className="h-3 w-3" />
            ) : (
              <AlertTriangle className="h-3 w-3" />
            )}
            {passed ? (hasWarnings ? "passed with notes" : "all checks passed") : "issues found"}
          </span>
        </div>

        <div className="mt-4 flex items-center gap-1 border-t border-zinc-200 pt-3 dark:border-white/[0.05]">
          {TABS.map((item) => {
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setTab(item.id)}
                className={`tab-button ${tab === item.id ? "tab-button-active" : ""}`}
              >
                {item.label}
              </button>
            );
          })}
          <span className="ml-auto font-mono text-[8px] uppercase tracking-[0.16em] text-zinc-400 dark:text-zinc-700">
            nbformat 4.5
          </span>
        </div>
      </div>

      <div className="p-4 sm:p-5">
        {tab === "notebook" ? (
          <div className="notebook-scroll">
            {cells.map((cell, index) => (
              <CellCard key={cell.id ?? index} cell={cell} index={index} />
            ))}
          </div>
        ) : null}

        {tab === "checks" ? (
          <div className="space-y-4">
            <ValidationChecks validation={validation} />

            <div className="grid grid-cols-3 gap-2">
              {[
                { label: "cells", value: validation.stats?.cells ?? cells.length },
                { label: "code cells", value: validation.stats?.code_cells ?? codeCells },
                { label: "python lines", value: validation.stats?.python_lines ?? "—" },
              ].map((stat) => (
                <div
                  key={stat.label}
                  className="rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-center dark:border-white/[0.06] dark:bg-white/[0.02]"
                >
                  <div className="font-mono text-sm font-semibold text-zinc-900 dark:text-white">
                    {stat.value}
                  </div>
                  <div className="mt-0.5 text-[9px] uppercase tracking-wide text-zinc-500 dark:text-zinc-600">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>

            {passed ? (
              <div className="flex items-start gap-2.5 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.05] px-3 py-2.5">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400/80" />
                <div>
                  <div className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-300">
                    Validation gate passed
                  </div>
                  <p className="mt-0.5 text-[10px] leading-relaxed text-zinc-500">
                    The notebook was parsed and safety-checked before packaging.
                  </p>
                </div>
              </div>
            ) : null}

            <FindingList findings={validation.errors} tone="error" />
            <FindingList findings={validation.warnings} tone="warning" />

            {generation.fallback_reason ? (
              <div className="flex items-start gap-2.5 rounded-xl border border-ember-300/20 bg-ember-300/[0.05] px-3 py-2.5">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-ember-600 dark:text-ember-300" />
                <div>
                  <div className="text-[11px] font-semibold text-ember-600 dark:text-ember-300">
                    Template fallback used
                  </div>
                  <p className="mt-0.5 text-[10px] leading-relaxed text-zinc-500">
                    {generation.fallback_reason}
                  </p>
                </div>
              </div>
            ) : null}

            {generation.notes ? (
              <div className="rounded-xl border border-zinc-200 bg-white px-3 py-2.5 dark:border-white/[0.06] dark:bg-white/[0.02]">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-zinc-500">
                  LLM design notes
                </div>
                <p className="mt-1 text-[10.5px] leading-relaxed text-zinc-600 dark:text-zinc-400">
                  {generation.notes}
                </p>
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === "license" ? (
          <div className="space-y-3">
            <div className="rounded-2xl border border-ember-300/20 bg-gradient-to-br from-ember-300/[0.08] to-transparent p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-ember-300/20 bg-ember-300/10 text-ember-600 dark:text-ember-300">
                    <Scale className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wide text-zinc-500">
                      Dataset license
                    </div>
                    <div className="text-sm font-semibold text-zinc-900 dark:text-white">
                      {license.name}
                    </div>
                  </div>
                </div>
                <a
                  href={license.url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary text-[10px]"
                >
                  View
                </a>
              </div>
              <p className="mt-3 text-[10.5px] leading-relaxed text-zinc-600 dark:text-zinc-400">
                {license.notes}
              </p>
            </div>

            <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-white/[0.06]">
              {[
                ["Dataset", meta.dataset_label],
                ["Attribution", license.attribution],
                ["Commercial use", license.commercial_use ? "Yes" : "Check upstream terms"],
                ["License URL", license.url],
                ["Source", meta.dataset_source ?? meta.dataset],
              ].map(([label, value], index) => (
                <div
                  key={label}
                  className={`grid grid-cols-[110px_1fr] gap-3 px-3 py-2.5 ${
                    index % 2 === 0
                      ? "bg-zinc-50 dark:bg-white/[0.02]"
                      : "bg-transparent"
                  }`}
                >
                  <span className="text-[10px] uppercase tracking-wide text-zinc-500 dark:text-zinc-600">
                    {label}
                  </span>
                  <span className="break-words text-[10.5px] text-zinc-600 dark:text-zinc-400">
                    {value}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex items-start gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 dark:border-white/[0.06] dark:bg-white/[0.02]">
              <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ember-600 dark:text-ember-300" />
              <p className="text-[10px] leading-relaxed text-zinc-500">
                The license snapshot is embedded in cell 1 and written to
                `/content/outputs/DATASET_LICENSE.txt` by the export cell. Verify
                upstream terms before redistribution.
              </p>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
