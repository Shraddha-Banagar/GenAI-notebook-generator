import { useCallback, useEffect, useRef, useState } from "react";
import { ServerOff } from "lucide-react";
import Header from "./components/Header.jsx";
import Hero from "./components/Hero.jsx";
import ModelSelector from "./components/ModelSelector.jsx";
import DatasetSelector from "./components/DatasetSelector.jsx";
import SettingsPanel from "./components/SettingsPanel.jsx";
import GeneratePanel from "./components/GeneratePanel.jsx";
import ResultPanel from "./components/ResultPanel.jsx";
import SamplesPanel from "./components/SamplesPanel.jsx";
import Footer from "./components/Footer.jsx";
import { generateNotebook, getCatalog, getSamples } from "./lib/api.js";

const PROGRESS_STEPS = [
  "Scaffolding nbformat cells",
  "Selecting the vetted section template",
  "Requesting LLM code (when enabled)",
  "Running AST safety + TF2 checks",
  "Injecting license and BLIP cell",
  "Packaging the .ipynb",
];

function WorkspaceSkeleton() {
  return (
    <div className="space-y-5">
      {[0, 1, 2].map((index) => (
        <div key={index} className="glass-panel panel-padding">
          <div className="h-3 w-28 animate-pulse rounded-full bg-zinc-200 dark:bg-white/[0.06]" />
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div
                key={item}
                className="h-36 animate-pulse rounded-2xl border border-zinc-200 bg-zinc-100/60 dark:border-white/[0.05] dark:bg-white/[0.02]"
                style={{ animationDelay: `${(index * 3 + item) * 80}ms` }}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [samples, setSamples] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [samplesLoading, setSamplesLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [selectedModel, setSelectedModel] = useState("dcgan");
  const [selectedDataset, setSelectedDataset] = useState("fashion_mnist");
  const [epochs, setEpochs] = useState(5);
  const [batchSize, setBatchSize] = useState(64);
  const [useLlm, setUseLlm] = useState(true);

  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [progressIndex, setProgressIndex] = useState(0);

  const resultRef = useRef(null);

  const loadData = useCallback(async () => {
    setCatalogLoading(true);
    setLoadError("");
    try {
      const nextCatalog = await getCatalog();
      setCatalog(nextCatalog);
      setSelectedModel((current) =>
        nextCatalog.models.some((model) => model.id === current)
          ? current
          : nextCatalog.models[0]?.id ?? "dcgan",
      );
      setSelectedDataset((current) => {
        const model =
          nextCatalog.models.find((item) => item.id === selectedModel) ??
          nextCatalog.models[0];
        if (model?.datasets.includes(current)) return current;
        return model?.default_dataset ?? model?.datasets[0] ?? "fashion_mnist";
      });
    } catch (err) {
      setLoadError(err.message || "Could not reach the API.");
    } finally {
      setCatalogLoading(false);
    }

    setSamplesLoading(true);
    try {
      const samplePayload = await getSamples();
      setSamples(samplePayload.samples ?? []);
    } catch {
      setSamples([]);
    } finally {
      setSamplesLoading(false);
    }
  }, [selectedModel]);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!catalog) return;
    const model = catalog.models.find((item) => item.id === selectedModel);
    if (!model) return;
    if (!model.datasets.includes(selectedDataset)) {
      const nextDataset = model.default_dataset ?? model.datasets[0];
      setSelectedDataset(nextDataset);
      const dataset = catalog.datasets.find((item) => item.id === nextDataset);
      if (dataset?.default_batch_size) setBatchSize(dataset.default_batch_size);
    }
  }, [catalog, selectedModel, selectedDataset]);

  useEffect(() => {
    if (status !== "generating") {
      setProgressIndex(0);
      return undefined;
    }
    setProgressIndex(0);
    const timer = setInterval(() => {
      setProgressIndex((index) => (index + 1) % PROGRESS_STEPS.length);
    }, 1400);
    return () => clearInterval(timer);
  }, [status]);

  const models = catalog?.models ?? [];
  const datasets = catalog?.datasets ?? [];
  const selectedModelData = models.find((model) => model.id === selectedModel) ?? models[0];
  const selectedDatasetData = datasets.find((dataset) => dataset.id === selectedDataset);
  const compatibleDatasets = selectedModelData
    ? selectedModelData.datasets
        .map((id) => datasets.find((dataset) => dataset.id === id))
        .filter(Boolean)
    : [];

  function handleModelSelect(model) {
    setSelectedModel(model.id);
    setError("");
    setResult(null);
    setStatus("idle");
    if (!model.datasets.includes(selectedDataset)) {
      const nextDataset = model.default_dataset ?? model.datasets[0];
      setSelectedDataset(nextDataset);
      const dataset = datasets.find((item) => item.id === nextDataset);
      if (dataset?.default_batch_size) setBatchSize(dataset.default_batch_size);
    }
  }

  function handleDatasetSelect(dataset) {
    setSelectedDataset(dataset.id);
    if (dataset.default_batch_size) setBatchSize(dataset.default_batch_size);
    setError("");
    setResult(null);
    setStatus("idle");
  }

  function scrollToResult() {
    resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleGenerate() {
    if (!selectedModelData || !selectedDatasetData) return;
    setStatus("generating");
    setError("");
    setResult(null);
    requestAnimationFrame(scrollToResult);

    try {
      const response = await generateNotebook({
        model: selectedModel,
        dataset: selectedDataset,
        epochs,
        batch_size: batchSize,
        use_llm: useLlm,
      });
      setResult(response);
      setStatus("success");
    } catch (err) {
      setError(err.message || "The generator returned an unexpected error.");
      setStatus("error");
    }
  }

  const summary =
    selectedModelData && selectedDatasetData
      ? `${selectedModelData.label} · ${selectedDatasetData.label}`
      : undefined;

  return (
    <>
      <div className="mesh-overlay" />
      <div id="top" className="relative z-10 min-h-screen">
        <Header online={!loadError} />

        <main className="mx-auto max-w-7xl px-4 pb-4 sm:px-6 lg:px-8">
          <Hero />

          <section id="generator" className="scroll-mt-24 pt-14">
            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <div className="space-y-5">
                {loadError ? (
                  <div className="glass-panel panel-padding">
                    <div className="flex items-start gap-3">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-ember-500/25 bg-ember-500/10 text-ember-400">
                        <ServerOff className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <h2 className="text-base font-semibold text-zinc-900 dark:text-white">
                          Backend API is not reachable
                        </h2>
                        <p className="mt-1 text-sm leading-relaxed text-zinc-500">
                          Start the FastAPI server, then retry. The UI expects it on
                          `http://127.0.0.1:8000`.
                        </p>
                        <pre className="mt-3 overflow-x-auto rounded-xl border border-zinc-200 bg-zinc-100 px-3 py-2.5 font-mono text-[11px] text-ember-600/90 dark:border-white/[0.06] dark:bg-ink-900 dark:text-ember-300/90">
{`cd backend
uvicorn app.main:app --reload --port 8000`}
                        </pre>
                        <p className="mt-2 text-[10.5px] text-zinc-500 dark:text-zinc-600">
                          {loadError}
                        </p>
                        <button
                          type="button"
                          onClick={loadData}
                          className="btn-secondary mt-4 text-[11px]"
                        >
                          Retry connection
                        </button>
                      </div>
                    </div>
                  </div>
                ) : catalogLoading ? (
                  <WorkspaceSkeleton />
                ) : (
                  <>
                    <ModelSelector
                      models={models}
                      selected={selectedModel}
                      onSelect={handleModelSelect}
                    />
                    <DatasetSelector
                      datasets={compatibleDatasets}
                      selected={selectedDataset}
                      onSelect={handleDatasetSelect}
                    />
                    <SettingsPanel
                      epochs={epochs}
                      batchSize={batchSize}
                      useLlm={useLlm}
                      model={selectedModelData}
                      onEpochsChange={setEpochs}
                      onBatchChange={setBatchSize}
                      onLlmChange={setUseLlm}
                    />
                    <GeneratePanel
                      onGenerate={handleGenerate}
                      status={status}
                      error={error}
                      progressLabel={PROGRESS_STEPS[progressIndex]}
                      summary={summary}
                    />
                  </>
                )}
              </div>

              <aside ref={resultRef} className="scroll-mt-24 space-y-5 xl:sticky xl:top-20 xl:self-start">
                <ResultPanel result={result} status={status} />
                <SamplesPanel samples={samples} loading={samplesLoading} />
              </aside>
            </div>
          </section>

          <Footer />
        </main>
      </div>
    </>
  );
}
