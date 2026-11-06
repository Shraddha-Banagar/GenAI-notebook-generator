import { useEffect, useRef, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Moon,
  ShieldCheck,
  Sun,
  Wifi,
  WifiOff,
} from "lucide-react";
import { apiBase } from "../lib/api.js";

function SettingRow({ icon: Icon, label, value, accent = false }) {
  return (
    <div className="flex items-center gap-3 rounded-xl px-2.5 py-2.5 transition hover:bg-zinc-100 dark:hover:bg-white/[0.03]">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-zinc-100 text-ember-600 dark:border-white/[0.06] dark:bg-white/[0.03] dark:text-ember-300">
        <Icon className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0 flex-1 text-[11px] text-zinc-600 dark:text-zinc-400">
        {label}
      </span>
      <span
        className={`truncate font-mono text-[10px] ${
          accent
            ? "text-ember-600 dark:text-ember-300"
            : "text-zinc-700 dark:text-zinc-300"
        }`}
      >
        {value}
      </span>
    </div>
  );
}

const HOW_TO_STEPS = [
  "Pick a model from the catalog on the left.",
  "Choose a licensed dataset that is compatible with it.",
  "Tune epochs and batch size to match your runtime budget.",
  "Generate the notebook and review the validation checks.",
  "Download the .ipynb or open it directly in Colab.",
];

export default function Header({ online = true }) {
  const [open, setOpen] = useState(false);
  const [howOpen, setHowOpen] = useState(false);
  const [isDark, setIsDark] = useState(() =>
    typeof document === "undefined"
      ? true
      : document.documentElement.classList.contains("dark"),
  );
  const menuRef = useRef(null);
  const endpoint = apiBase() || "http://127.0.0.1:8000";

  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch (error) {
      // Ignore storage failures (private mode, etc.)
    }
  }

  useEffect(() => {
    if (!open && !howOpen) return undefined;

    function handlePointerDown(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false);
        setHowOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setOpen(false);
        setHowOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, howOpen]);

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200/80 bg-white/80 backdrop-blur-2xl dark:border-white/[0.06] dark:bg-ink-950/70">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <a href="#top" className="group flex items-center gap-3">
          <img
            src="/favicon.svg"
            alt="GenAI Notebook Generator logo"
            className="h-9 w-9 rounded-xl shadow-glow-soft"
          />
          <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-white">
            GenAI Notebook{" "}
            <span className="text-ember-600 dark:text-ember-400">Generator</span>
          </span>
        </a>

        <div className="flex items-center gap-2" ref={menuRef}>
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setHowOpen((value) => !value);
                setOpen(false);
              }}
              aria-label="How to use"
              aria-haspopup="dialog"
              aria-expanded={howOpen}
              className={`flex h-10 items-center rounded-xl border px-4 text-[12px] font-medium transition hover:opacity-90 ${
                howOpen
                  ? "border-ember-500/40 bg-ember-500/10 text-ember-600 dark:text-ember-300"
                  : "border-zinc-200 bg-white text-zinc-700 hover:border-ember-500/30 hover:bg-ember-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-zinc-300 dark:hover:border-ember-400/30 dark:hover:bg-white/[0.05]"
              }`}
            >
              How
            </button>

            {howOpen ? (
              <div
                role="dialog"
                aria-label="How to use"
                className="absolute right-0 top-full z-50 mt-3 w-80 max-w-[calc(100vw-2rem)] animate-fade-up overflow-hidden rounded-2xl border border-zinc-200 bg-white/95 shadow-card-light backdrop-blur-2xl dark:border-white/10 dark:bg-ink-900/95 dark:shadow-card"
              >
                <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-white/[0.06]">
                  <div>
                    <div className="text-[11px] font-semibold text-zinc-900 dark:text-white">
                      How to use
                    </div>
                    <div className="mt-0.5 font-mono text-[8px] uppercase tracking-[0.16em] text-zinc-500 dark:text-zinc-600">
                      Five quick steps
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => setHowOpen(false)}
                    aria-label="Close how to use"
                    className="rounded-lg px-2 py-1 text-[10px] font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 hover:opacity-90 dark:hover:bg-white/[0.05] dark:hover:text-white"
                  >
                    Close
                  </button>
                </div>

                <ol className="space-y-2.5 p-4">
                  {HOW_TO_STEPS.map((step, index) => (
                    <li key={step} className="flex items-start gap-3">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-ember-500/15 font-mono text-[10px] font-semibold text-ember-600 dark:text-ember-300">
                        {index + 1}
                      </span>
                      <span className="text-[11px] leading-relaxed text-zinc-600 dark:text-zinc-400">
                        {step}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setOpen((value) => !value);
                setHowOpen(false);
              }}
              aria-label="Settings and technical details"
              aria-haspopup="dialog"
              aria-expanded={open}
              className={`flex h-10 items-center rounded-xl border px-4 text-[12px] font-medium transition hover:opacity-90 ${
                open
                  ? "border-ember-500/40 bg-ember-500/10 text-ember-600 dark:text-ember-300"
                  : "border-zinc-200 bg-white text-zinc-700 hover:border-ember-500/30 hover:bg-ember-50 dark:border-white/10 dark:bg-white/[0.03] dark:text-zinc-300 dark:hover:border-ember-400/30 dark:hover:bg-white/[0.05]"
              }`}
            >
              Settings
            </button>

          {open ? (
            <div
              role="dialog"
              aria-label="Settings"
              className="absolute right-0 top-full z-50 mt-3 w-72 max-w-[calc(100vw-2rem)] animate-fade-up overflow-hidden rounded-2xl border border-zinc-200 bg-white/95 shadow-card-light backdrop-blur-2xl dark:border-white/10 dark:bg-ink-900/95 dark:shadow-card"
            >
              <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-white/[0.06]">
                <div>
                  <div className="text-[11px] font-semibold text-zinc-900 dark:text-white">
                    Settings
                  </div>
                  <div className="mt-0.5 font-mono text-[8px] uppercase tracking-[0.16em] text-zinc-500 dark:text-zinc-600">
                    Technical details
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  aria-label="Close settings"
                  className="rounded-lg px-2 py-1 text-[10px] font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 hover:opacity-90 dark:hover:bg-white/[0.05] dark:hover:text-white"
                >
                  Close
                </button>
              </div>

              <div className="space-y-0.5 p-2">
                <div className="flex items-center gap-3 rounded-xl px-2.5 py-2.5">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-zinc-100 text-ember-600 dark:border-white/[0.06] dark:bg-white/[0.03] dark:text-ember-300">
                    {isDark ? (
                      <Moon className="h-3.5 w-3.5" />
                    ) : (
                      <Sun className="h-3.5 w-3.5" />
                    )}
                  </span>
                  <span className="min-w-0 flex-1 text-[11px] text-zinc-600 dark:text-zinc-400">
                    Theme
                  </span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={isDark}
                    aria-label="Toggle dark theme"
                    onClick={toggleTheme}
                    className={`relative h-6 w-11 shrink-0 rounded-full border transition duration-300 ${
                      isDark
                        ? "border-ember-300/30 bg-ember-gradient"
                        : "border-zinc-300 bg-zinc-200"
                    }`}
                  >
                    <span
                      className={`absolute top-0.5 h-[18px] w-[18px] rounded-full bg-white shadow-sm transition-transform duration-300 ${
                        isDark ? "translate-x-[22px]" : "translate-x-0.5"
                      }`}
                    />
                  </button>
                </div>
                <div className="flex items-center gap-3 rounded-xl px-2.5 py-2.5">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-zinc-200 bg-zinc-100 text-ember-600 dark:border-white/[0.06] dark:bg-white/[0.03] dark:text-ember-300">
                    <Activity className="h-3.5 w-3.5" />
                  </span>
                  <span className="flex-1 text-[11px] text-zinc-600 dark:text-zinc-400">
                    Engine
                  </span>
                  <span className="flex items-center gap-1.5 font-mono text-[10px] text-zinc-700 dark:text-zinc-300">
                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        online
                          ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                          : "bg-ember-500"
                      }`}
                    />
                    {online ? "Online" : "Offline"}
                  </span>
                </div>
                <SettingRow
                  icon={online ? Wifi : WifiOff}
                  label="API endpoint"
                  value={endpoint}
                />
                <SettingRow icon={CheckCircle2} label="Runtime" value="TF2 / Keras" />
                <SettingRow
                  icon={ShieldCheck}
                  label="Validation gate"
                  value="AST + TF2"
                  accent
                />
                <SettingRow
                  icon={CheckCircle2}
                  label="Notebook format"
                  value="nbformat 4.5"
                />
              </div>

              <div className="flex items-center justify-between border-t border-zinc-200 px-4 py-2.5 dark:border-white/[0.06]">
                <span className="text-[10px] text-zinc-500 dark:text-zinc-600">
                  Version
                </span>
                <span className="font-mono text-[10px] text-ember-600/80 dark:text-ember-300/80">
                  v1.0.0
                </span>
              </div>
            </div>
          ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
