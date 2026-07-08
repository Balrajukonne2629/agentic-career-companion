import { useEffect, useMemo, useState } from 'react';
import AmbientBackground from './components/AmbientBackground';
import Footer from './components/Footer';
import PipelinePreview from './components/PipelinePreview';
import TopBar from './components/TopBar';
import WorkspaceCard from './components/WorkspaceCard';
import {
  STORAGE_KEYS,
  createInitialPipelineRows,
  getPipelinePreviewFromRows,
  loadingMockStages,
  pipelineMockSnippets,
  pipelinePreviewStages,
} from './data/workspaceCopy';
import { pipelineSteps } from './services/pipelineService';

function readStorage(key, fallback) {
  if (typeof window === 'undefined') return fallback;
  try {
    const value = window.localStorage.getItem(key);
    return value ? value : fallback;
  } catch {
    return fallback;
  }
}

function getErrorMessage(error) {
  if (!error) return 'Pipeline paused. Please retry this step to continue.';
  if (typeof error === 'string') return error;
  return error.message || error.data?.message || 'Pipeline paused. Please retry this step to continue.';
}

function createEmptyResults() {
  return {
    validation: null,
    profileAnalysis: null,
    recommendations: null,
    skillGap: null,
    roadmap: null,
  };
}

function App() {
  const prefersDark = typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches;
  const [theme, setTheme] = useState(() => readStorage(STORAGE_KEYS.theme, prefersDark ? 'dark' : 'light'));
  const [mode, setMode] = useState(() => readStorage(STORAGE_KEYS.mode, 'speak'));
  const [draft, setDraft] = useState('');
  const [screen, setScreen] = useState('compose');
  const [pipelineRows, setPipelineRows] = useState(() => createInitialPipelineRows());
  const [activeIndex, setActiveIndex] = useState(null);
  const [errorIndex, setErrorIndex] = useState(null);
  const [lastTranscript, setLastTranscript] = useState('');
  const [pipelineResults, setPipelineResults] = useState(() => createEmptyResults());

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(STORAGE_KEYS.theme, theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(STORAGE_KEYS.mode, mode);
  }, [mode]);

  const previewRows = useMemo(
    () =>
      getPipelinePreviewFromRows(
        pipelineRows.length
          ? pipelineRows
          : loadingMockStages.map((stage, index) => ({
              key: pipelinePreviewStages[index]?.key ?? stage.label,
              label: stage.label,
              state: stage.status,
            })),
      ),
    [pipelineRows],
  );

  const runPipelineFrom = async (startIndex, transcript, previousResults = pipelineResults) => {
    const workingResults = { ...previousResults };
    setScreen('pipeline');
    setErrorIndex(null);

    setPipelineRows((currentRows) =>
      currentRows.map((row, index) => ({
        ...row,
        state: index < startIndex ? 'done' : index === startIndex ? 'active' : 'idle',
        snippet: index < startIndex ? row.snippet : '',
      })),
    );

    for (let index = startIndex; index < pipelineSteps.length; index += 1) {
      const step = pipelineSteps[index];
      setActiveIndex(index);
      setPipelineRows((currentRows) =>
        currentRows.map((row, rowIndex) => ({
          ...row,
          state: rowIndex < index ? 'done' : rowIndex === index ? 'active' : 'idle',
        })),
      );

      try {
        const result = await step.run({ transcript, results: workingResults });

        if (step.key === 'validation' && result?.status && result.status !== 'complete') {
          throw {
            message: result.message || `Validation needs more information: ${(result.missing_fields || []).join(', ')}`,
            data: result,
          };
        }

        workingResults[step.resultKey] = result;
        setPipelineResults({ ...workingResults });
        setPipelineRows((currentRows) =>
          currentRows.map((row, rowIndex) =>
            rowIndex === index
              ? {
                  ...row,
                  state: 'done',
                  snippet: pipelineMockSnippets[row.key] || 'Step completed successfully.',
                }
              : row,
          ),
        );
      } catch (error) {
        const message = getErrorMessage(error);
        setErrorIndex(index);
        setActiveIndex(null);
        setPipelineRows((currentRows) =>
          currentRows.map((row, rowIndex) =>
            rowIndex === index
              ? {
                  ...row,
                  state: 'error',
                  snippet: message,
                }
              : rowIndex > index
                ? { ...row, state: 'idle', snippet: '' }
                : row,
          ),
        );
        return;
      }
    }

    setActiveIndex(null);
    setErrorIndex(null);
    setScreen('dashboard');
  };

  const handleStartPipeline = (payload) => {
    const transcript = String(payload || '').trim();
    setLastTranscript(transcript);
    setPipelineResults(createEmptyResults());
    setPipelineRows(createInitialPipelineRows());
    void runPipelineFrom(0, transcript, createEmptyResults());
  };

  const handleRetryStep = (index) => {
    if (!lastTranscript) return;

    const nextResults = { ...pipelineResults };
    pipelineSteps.slice(index).forEach((step) => {
      nextResults[step.resultKey] = null;
    });
    setPipelineResults(nextResults);
    void runPipelineFrom(index, lastTranscript, nextResults);
  };

  const handleSimulateError = (index) => {
    setPipelineRows((currentRows) =>
      currentRows.map((row, currentIndex) =>
        currentIndex === index
          ? {
              ...row,
              state: 'error',
              snippet: 'Pipeline paused. Retry this step to continue the mock flow.',
            }
          : row,
      ),
    );
    setErrorIndex(index);
    setActiveIndex(null);
  };

  const reduceMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  return (
    <div className="relative isolate min-h-screen overflow-hidden bg-transparent text-zinc-700 transition-colors duration-300 dark:text-zinc-200">
      <AmbientBackground />

      <div className="relative z-10">
        <TopBar theme={theme} onToggleTheme={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))} />
      </div>

      <main className={`relative z-10 mx-auto flex w-full flex-col gap-4 px-4 py-8 sm:px-6 sm:py-10 lg:px-0 lg:py-12 ${screen === 'dashboard' ? 'max-w-6xl' : 'max-w-2xl'}`}>
        <WorkspaceCard
          mode={mode}
          onModeChange={setMode}
          screen={screen}
          pipelineRows={pipelineRows}
          pipelineResults={pipelineResults}
          onStartPipeline={handleStartPipeline}
          onRetryStep={handleRetryStep}
          onSimulateError={handleSimulateError}
          draft={draft}
          setDraft={setDraft}
          reducedMotion={reduceMotion}
        />

        <PipelinePreview stages={previewRows} />
      </main>

      <Footer />
    </div>
  );
}

export default App;
