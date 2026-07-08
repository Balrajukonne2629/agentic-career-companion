import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, Mic, Pause, RotateCcw, SendHorizontal, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { introTags, MIN_SPEAK_CHARS, speakSampleTranscript } from '../data/workspaceCopy';

const SHOW_DEV_CONTROLS = import.meta.env.DEV;

/**
 * @param {{ onContinue: (transcript: string) => void, reducedMotion?: boolean }} props
 */
function SpeakMode({ onContinue, reducedMotion = false }) {
  const [phase, setPhase] = useState('onboarding');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [transcript, setTranscript] = useState('');
  const [permissionError, setPermissionError] = useState(false);

  useEffect(() => {
    if (phase !== 'recording') {
      return undefined;
    }

    const timer = setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    const autoStop = setTimeout(() => {
      setTranscript(speakSampleTranscript);
      setPhase('review');
    }, 6200);

    return () => {
      clearInterval(timer);
      clearTimeout(autoStop);
    };
  }, [phase]);

  const bars = useMemo(() => [34, 72, 44, 96, 58, 116, 48, 88, 64, 104, 42, 78, 54, 92, 38, 68], []);

  const formatTimer = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`;
  };

  const handleStart = () => {
    setPermissionError(false);
    setElapsedSeconds(0);
    setPhase('recording');
  };

  const handleStop = () => {
    setTranscript(speakSampleTranscript);
    setPhase('review');
  };

  const handleSimulatePermissionDenied = () => {
    setPermissionError(true);
    setPhase('onboarding');
  };

  const canContinue = transcript.trim().length >= MIN_SPEAK_CHARS;

  return (
    <AnimatePresence mode="wait" initial={false}>
      {phase === 'onboarding' ? (
        <motion.div
          key="onboarding"
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="space-y-5"
          id="speak-panel"
          role="tabpanel"
          aria-labelledby="speak-tab"
        >
          <section className="relative overflow-hidden rounded-3xl border border-zinc-200/90 bg-white/92 p-6 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/82 dark:shadow-glass sm:p-7">
            <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-2xl">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-blue-200/80 bg-blue-50 text-ibm-blue shadow-sm dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
                  <Mic className="h-5 w-5" aria-hidden="true" />
                </div>
                <h2 className="mt-5 text-2xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">Introduce yourself naturally</h2>
                <p className="mt-2 text-sm leading-7 text-zinc-600 dark:text-zinc-400">
                  Mention the details that help the AI understand your current profile and career direction.
                </p>
              </div>
              <span className="inline-flex w-fit items-center gap-2 rounded-full border border-zinc-200/70 bg-white/70 px-4 py-2 text-sm font-semibold text-zinc-600 shadow-sm dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-300">
                <Sparkles className="h-4 w-4 text-ibm-blue dark:text-blue-300" aria-hidden="true" />
                Expected time: 30-60 seconds
              </span>
            </div>

            <div className="relative mt-6 flex flex-wrap gap-2">
              {introTags.map((tag) => (
                <span key={tag} className="rounded-full border border-zinc-200/80 bg-white/70 px-3 py-2 text-xs font-semibold text-zinc-600 shadow-sm dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-300">
                  {tag}
                </span>
              ))}
            </div>

            {permissionError ? (
              <div className="relative mt-5 rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-900 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-200">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  <div className="flex-1">
                    Microphone permission was denied. You can retry when you are ready.
                    <button type="button" onClick={() => setPermissionError(false)} className="ml-2 underline underline-offset-4">
                      Retry
                    </button>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="relative mt-7 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleStart}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-zinc-950 px-6 py-3 text-sm font-semibold text-white shadow-[0_18px_40px_-18px_rgba(15,98,254,0.75)] transition hover:-translate-y-0.5 hover:bg-ibm-blue focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:bg-white dark:text-zinc-950 dark:hover:bg-blue-100"
              >
                <Mic className="h-4 w-4" aria-hidden="true" />
                Start Your Introduction
              </button>
              {SHOW_DEV_CONTROLS ? (
                <button
                  type="button"
                  onClick={handleSimulatePermissionDenied}
                  className="inline-flex min-h-12 items-center justify-center rounded-full border border-zinc-200/80 bg-white/70 px-5 py-3 text-sm font-semibold text-zinc-600 transition hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-300 dark:hover:text-zinc-50"
                >
                  Mock permission issue
                </button>
              ) : null}
            </div>
          </section>
        </motion.div>
      ) : null}

      {phase === 'recording' ? (
        <motion.div
          key="recording"
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="space-y-5"
          id="speak-panel"
          role="tabpanel"
          aria-labelledby="speak-tab"
        >
          <section className="relative min-h-[27rem] overflow-hidden rounded-3xl border border-blue-200/60 bg-[radial-gradient(circle_at_50%_0%,rgba(15,98,254,0.18),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.86),rgba(255,255,255,0.62))] p-6 shadow-float backdrop-blur-2xl dark:border-blue-400/20 dark:bg-[radial-gradient(circle_at_50%_0%,rgba(96,165,250,0.24),transparent_42%),linear-gradient(180deg,rgba(24,24,27,0.86),rgba(9,9,11,0.72))] sm:p-8">
            <div className="relative z-10 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ibm-blue dark:text-blue-300">Recording</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">Speak naturally</h2>
              </div>
              <div className="rounded-full border border-white/70 bg-white/70 px-4 py-2 font-mono text-sm font-semibold text-zinc-800 shadow-sm dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-100">
                {formatTimer(elapsedSeconds)}
              </div>
            </div>

            <div className="relative z-10 mt-10 flex flex-col items-center justify-center gap-8">
              <div className="relative flex h-28 w-28 items-center justify-center">
                {!reducedMotion ? (
                  <>
                    <motion.span className="absolute inset-0 rounded-full bg-ibm-blue/20" animate={{ scale: [1, 1.45, 1], opacity: [0.5, 0, 0.5] }} transition={{ duration: 1.8, repeat: Infinity, ease: 'easeOut' }} />
                    <motion.span className="absolute inset-3 rounded-full bg-blue-400/20" animate={{ scale: [1, 1.28, 1], opacity: [0.45, 0.1, 0.45] }} transition={{ duration: 1.4, repeat: Infinity, ease: 'easeOut' }} />
                  </>
                ) : null}
                <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-zinc-950 text-white shadow-[0_0_60px_rgba(15,98,254,0.42)] dark:bg-white dark:text-zinc-950">
                  <Mic className="h-8 w-8" aria-hidden="true" />
                </div>
              </div>

              <div className="flex h-32 w-full max-w-2xl items-center justify-center gap-2 rounded-[2rem] border border-white/70 bg-white/50 px-5 py-5 shadow-inner dark:border-white/10 dark:bg-zinc-950/50" aria-hidden="true">
                {bars.map((bar, index) => (
                  <motion.span
                    key={index}
                    className="w-2 rounded-full bg-gradient-to-t from-ibm-blue to-blue-300 shadow-[0_0_18px_rgba(15,98,254,0.28)]"
                    style={{ height: `${bar}px`, transformOrigin: 'center' }}
                    animate={reducedMotion ? { opacity: 1 } : { opacity: [0.5, 1, 0.55], scaleY: [0.58, 1.08, 0.72] }}
                    transition={reducedMotion ? { duration: 0 } : { duration: 0.95, repeat: Infinity, ease: 'easeInOut', delay: index * 0.045 }}
                  />
                ))}
              </div>
            </div>

            <div className="relative z-10 mt-8 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={handleStop}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-zinc-950 px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-ibm-blue focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:bg-white dark:text-zinc-950"
              >
                <Pause className="h-4 w-4" aria-hidden="true" />
                Stop Recording
              </button>
              <button
                type="button"
                onClick={() => setPhase('onboarding')}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full border border-white/70 bg-white/60 px-5 py-3 text-sm font-semibold text-zinc-600 transition hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-300 dark:hover:text-zinc-50"
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Re-record
              </button>
            </div>
          </section>
        </motion.div>
      ) : null}

      {phase === 'review' ? (
        <motion.div
          key="review"
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="space-y-5"
          id="speak-panel"
          role="tabpanel"
          aria-labelledby="speak-tab"
        >
          <section className="rounded-3xl border border-zinc-200/90 bg-white/92 p-6 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/82 dark:shadow-glass sm:p-7">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ibm-blue dark:text-blue-300">Transcript Preview</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">Review and edit your introduction</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                  Make any final changes before the agent pipeline starts.
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setPhase('onboarding');
                  setElapsedSeconds(0);
                  setTranscript('');
                }}
                className="inline-flex min-h-11 items-center justify-center gap-2 rounded-full border border-zinc-200/80 bg-white/70 px-4 py-2 text-sm font-semibold text-zinc-600 transition hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-300 dark:hover:text-zinc-50"
              >
                <RotateCcw className="h-4 w-4" aria-hidden="true" />
                Re-record
              </button>
            </div>

            <label className="sr-only" htmlFor="speak-transcript">Transcript preview</label>
            <textarea
              id="speak-transcript"
              value={transcript}
              onChange={(event) => setTranscript(event.target.value)}
              className="mt-6 min-h-56 w-full resize-y rounded-3xl border border-zinc-200/80 bg-white/70 p-5 text-sm leading-7 text-zinc-800 outline-none shadow-inner transition focus-visible:border-ibm-blue focus-visible:ring-2 focus-visible:ring-ibm-blue/20 dark:border-white/10 dark:bg-zinc-950/50 dark:text-zinc-100"
            />

            <div className="mt-4 flex flex-col gap-3 text-sm sm:flex-row sm:items-center sm:justify-between">
              <p className={`${canContinue ? 'text-zinc-500 dark:text-zinc-400' : 'text-amber-600 dark:text-amber-300'}`}>
                {canContinue ? 'Transcript ready to continue.' : `Add a bit more detail (${transcript.trim().length}/${MIN_SPEAK_CHARS} chars).`}
              </p>
              <button
                type="button"
                onClick={() => onContinue(transcript)}
                disabled={!canContinue}
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-zinc-950 px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-ibm-blue disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-500 disabled:shadow-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:bg-white dark:text-zinc-950 dark:hover:bg-blue-100"
              >
                Continue
                <SendHorizontal className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </section>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

export default SpeakMode;



