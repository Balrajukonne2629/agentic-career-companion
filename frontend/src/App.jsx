import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
  const [toasts, setToasts] = useState([]);
  const toastTimers = useRef([]);

  const showToast = useCallback((message, type = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev.slice(-2), { id, message, type }]);
    const timer = setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
    toastTimers.current.push(timer);
  }, []);

  useEffect(() => {
    const timers = toastTimers.current;
    return () => timers.forEach(clearTimeout);
  }, []);

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

      // Log step start and stage transitions
      if (index > 0) {
        console.log('%c↓', 'font-size: 16px; font-weight: bold; color: #757575;');
      }
      let stepName = step.key.toUpperCase();
      if (step.key === 'validation') stepName = 'VALIDATE';
      if (step.key === 'skillgap') stepName = 'SKILL GAP';
      if (step.key === 'roadmap') stepName = 'ROADMAP';

      console.group(`%c${stepName} - Entered`, 'font-size: 14px; font-weight: bold; color: #2196F3;');
      
      let inputPayload = {};
      if (step.key === 'validation') {
        inputPayload = {
          transcript,
          partialProfile: workingResults.validation?.partial_profile || null
        };
      } else if (step.key === 'profile') {
        inputPayload = { studentProfile: workingResults.validation?.profile };
      } else if (step.key === 'career') {
        inputPayload = {
          studentProfile: workingResults.validation?.profile,
          profileAnalysis: workingResults.profileAnalysis
        };
      } else if (step.key === 'skillgap') {
        inputPayload = {
          studentProfile: workingResults.validation?.profile,
          recommendations: workingResults.recommendations
        };
      } else if (step.key === 'roadmap') {
        inputPayload = {
          studentProfile: workingResults.validation?.profile,
          profileAnalysis: workingResults.profileAnalysis,
          skillGap: workingResults.skillGap,
          recommendations: workingResults.recommendations
        };
      }
      console.log('Input Payload (Entering Stage):', inputPayload);
      if (inputPayload.studentProfile) {
        console.log('Student Profile Table:');
        console.table(inputPayload.studentProfile);
      }
      console.groupEnd();

      try {
        const result = await step.run({ transcript, results: workingResults });

        // Success toast per step
        const successMessages = {
          validation: 'Profile successfully analyzed',
          profile:    'Career readiness profile generated',
          career:     'Career recommendations generated',
          skillgap:   'Skill gap analysis complete',
          roadmap:    'Personalized roadmap generated',
        };
        if (successMessages[step.key]) showToast(successMessages[step.key]);

        console.group(`%c${stepName} - Completed`, 'font-size: 12px; font-weight: bold; color: #4CAF50;');
        console.log('Output Payload (Leaving Stage):', result);
        console.groupEnd();

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
        console.group(`%c${stepName} - Failed`, 'font-size: 12px; font-weight: bold; color: #F44336;');
        console.error('Error in step:', error);
        console.groupEnd();
        if (step.key === 'validation' && error.data?.status === 'incomplete') {
          const result = error.data;
          workingResults['validation'] = result;
          setPipelineResults({ ...workingResults });
          setActiveIndex(null);
          setPipelineRows((currentRows) =>
            currentRows.map((row, rowIndex) =>
              rowIndex === index
                ? {
                    ...row,
                    state: 'incomplete',
                    snippet: 'Some required profile fields are missing.',
                    missingFields: result.missing_fields,
                    missingLabels: result.missing_labels,
                    partialProfile: result.partial_profile,
                  }
                : row,
            ),
          );
          return;
        }

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

  const handleSubmitIncomplete = (missingValues) => {
    if (!lastTranscript) return;

    const answerParts = Object.entries(missingValues)
      .filter(([_, val]) => val && String(val).trim() !== '')
      .map(([field, val]) => `My ${field.replace(/_/g, ' ')} is ${String(val).trim()}`);

    if (answerParts.length === 0) return;

    const appendedText = answerParts.join('. ') + '.';
    const newTranscript = `${lastTranscript} ${appendedText}`;
    setLastTranscript(newTranscript);

    // Re-run validation (index 0) with the new transcript
    void runPipelineFrom(0, newTranscript, pipelineResults);
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
    <div className="relative isolate min-h-screen overflow-hidden bg-transparent text-zinc-700 transition-colors duration-300 dark:text-zinc-200 print:h-auto print:overflow-visible">
      <div className="print:hidden">
        <AmbientBackground />
      </div>

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
          onSubmitIncomplete={handleSubmitIncomplete}
          onSimulateError={handleSimulateError}
          draft={draft}
          setDraft={setDraft}
          reducedMotion={reduceMotion}
        />

        <PipelinePreview stages={previewRows} />
      </main>

      <Footer />

      {/* Toast notifications */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="false"
        className="pointer-events-none fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2 print:hidden"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="pointer-events-auto flex items-center gap-3 rounded-2xl border border-emerald-200/80 bg-white/95 px-4 py-3 shadow-lg backdrop-blur-xl transition-all duration-300 dark:border-emerald-400/20 dark:bg-zinc-900/95"
            style={{ animation: 'toast-in 0.22s ease-out' }}
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-white text-xs">
              ✓
            </span>
            <p className="text-sm font-semibold text-zinc-800 dark:text-zinc-100">{toast.message}</p>
          </div>
        ))}
      </div>

      <style>{`
        @keyframes toast-in {
          from { opacity: 0; transform: translateY(8px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)   scale(1); }
        }
      `}</style>
    </div>
  );
}

export default App;
