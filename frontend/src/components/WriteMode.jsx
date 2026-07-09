import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, PenSquare, SendHorizontal } from 'lucide-react';
import { useMemo, useState } from 'react';
import { MAX_WRITE_CHARS, MIN_WRITE_CHARS, writeExample } from '../data/workspaceCopy';

/**
 * @param {{ value: string, onChange: (value: string) => void, onContinue: (value: string) => void, speechWarning?: boolean, reducedMotion?: boolean }} props
 */
function WriteMode({ value, onChange, onContinue, speechWarning = false, reducedMotion = false }) {
  const [focused, setFocused] = useState(false);

  const length = value.trim().length;
  const counterTone = useMemo(() => {
    if (length < MIN_WRITE_CHARS) return 'text-zinc-500 dark:text-zinc-400';
    if (length < 0.8 * MAX_WRITE_CHARS) return 'text-emerald-600 dark:text-emerald-300';
    return 'text-amber-600 dark:text-amber-300';
  }, [length]);

  const canContinue = length >= MIN_WRITE_CHARS;

  return (
    <motion.div
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="space-y-5"
      id="write-panel"
      role="tabpanel"
      aria-labelledby="write-tab"
    >
      <section className="relative overflow-hidden rounded-3xl border border-zinc-200/90 bg-white/92 p-6 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/82 dark:shadow-glass sm:p-7">
        <div className="relative flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ibm-blue dark:text-blue-300">Write Mode</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">Type your introduction</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              A few clear lines are enough. Include your year, skills, interests, CGPA, and career goal.
            </p>
          </div>
          <div className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-blue-200/80 bg-blue-50 text-ibm-blue shadow-sm dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
            <PenSquare className="h-5 w-5" aria-hidden="true" />
          </div>
        </div>

        {speechWarning && (
          <div className="relative mt-5 rounded-2xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-900 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-200">
            <div className="flex items-start gap-3">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <div className="flex-1">
                Speech recognition is not supported in your browser. Automatically switched to manual typing mode.
              </div>
            </div>
          </div>
        )}

        <div className={`relative mt-6 rounded-[1.75rem] border bg-white/70 p-5 shadow-inner transition dark:bg-zinc-950/50 ${focused ? 'border-ibm-blue ring-2 ring-ibm-blue/20' : 'border-zinc-200/80 dark:border-white/10'}`}>
          <label htmlFor="write-introduction" className="sr-only">
            Student introduction
          </label>

          <div className="relative">
            <AnimatePresence initial={false} mode="wait">
              {!focused && !value ? (
                <motion.p
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 0.82 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.18, ease: 'easeOut' }}
                  className="pointer-events-none absolute left-0 top-0 whitespace-pre-wrap text-sm leading-7 text-zinc-400 dark:text-zinc-500 sm:text-base"
                >
                  {writeExample}
                </motion.p>
              ) : null}
            </AnimatePresence>

            <textarea
              id="write-introduction"
              value={value}
              onChange={(event) => onChange(event.target.value.slice(0, MAX_WRITE_CHARS))}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              className="relative min-h-80 w-full resize-y bg-transparent text-sm leading-7 text-zinc-900 outline-none placeholder:text-transparent dark:text-zinc-100 sm:text-base"
              aria-describedby="write-helper write-counter"
            />
          </div>

          <div className="mt-4 flex flex-col gap-2 border-t border-zinc-200/70 pt-4 text-xs dark:border-white/10 sm:flex-row sm:items-center sm:justify-between">
            <p id="write-helper" className={canContinue ? 'text-zinc-500 dark:text-zinc-400' : 'text-amber-600 dark:text-amber-300'}>
              {canContinue ? 'Ready for profile analysis.' : `Add a bit more detail (${length}/${MIN_WRITE_CHARS} chars).`}
            </p>
            <p id="write-counter" className={`font-mono font-semibold ${counterTone}`}>
              {length}/{MAX_WRITE_CHARS}
            </p>
          </div>
        </div>

        <div className="relative mt-5 flex justify-end">
          <button
            type="button"
            onClick={() => onContinue(value)}
            disabled={!canContinue}
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-full bg-zinc-950 px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:bg-ibm-blue disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-500 disabled:shadow-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:bg-white dark:text-zinc-950 dark:hover:bg-blue-100"
          >
            Continue
            <SendHorizontal className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </section>
    </motion.div>
  );
}

export default WriteMode;


