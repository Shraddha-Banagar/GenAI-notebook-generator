import {
  AlertTriangle,
  Braces,
  CheckCircle2,
  Cpu,
  FileJson,
  Scale,
  ShieldCheck,
} from "lucide-react";

const CHECKS = [
  { key: "syntax", label: "Python syntax", detail: "ast.parse", icon: Braces },
  { key: "safety", label: "Safety policy", detail: "imports · calls · shell", icon: ShieldCheck },
  { key: "tf2", label: "TF2 compatibility", detail: "no TF1 / legacy Keras", icon: Cpu },
  { key: "structure", label: "nbformat 4.5", detail: "cells · metadata", icon: FileJson },
  { key: "license", label: "License cell", detail: "dataset disclosure", icon: Scale },
];

export default function ValidationChecks({ validation }) {
  if (!validation) return null;
  const checks = validation.checks ?? {};

  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {CHECKS.map((check) => {
        const status = checks[check.key] ?? "passed";
        const failed = status === "failed";
        const Icon = check.icon;
        return (
          <div
            key={check.key}
            className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 ${
              failed
                ? "border-ember-500/30 bg-ember-500/[0.08]"
                : "border-zinc-200 bg-white dark:border-white/[0.06] dark:bg-white/[0.02]"
            }`}
          >
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border ${
                failed
                  ? "border-ember-500/30 bg-ember-500/10 text-ember-600 dark:text-ember-400"
                  : "border-emerald-400/30 bg-emerald-400/10 text-emerald-600 dark:border-emerald-400/20 dark:text-emerald-400"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-[11px] font-medium text-zinc-800 dark:text-zinc-200">
                {check.label}
              </div>
              <div className="truncate font-mono text-[9px] text-zinc-500 dark:text-zinc-600">
                {check.detail}
              </div>
            </div>
            {failed ? (
              <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-ember-400" />
            ) : (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400/80" />
            )}
          </div>
        );
      })}
    </div>
  );
}
