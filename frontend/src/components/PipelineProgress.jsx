import { AlertCircle, Check, Circle, Loader2, RotateCcw } from 'lucide-react';

/**
 * @param {{ rows: Array<{ key: string, label: string, description: string, state: 'idle' | 'active' | 'done' | 'error', snippet: string }>, onRetry: (index: number) => void, onSimulateError: (index: number) => void }} props
 */
function PipelineProgress({ rows, onRetry, onSimulateError }) {
  const completedCount = rows.filter((row) => row.state === 'done').length;
  const activeIndex = rows.findIndex((row) => row.state === 'active');
  const progress = Math.min(100, ((completedCount + (activeIndex >= 0 ? 0.45 : 0)) / rows.length) * 100);

  const statusMeta = {
    idle: { label: 'Queued' },
    active: { label: 'Running' },
    done: { label: 'Complete' },
    error: { label: 'Needs retry' },
  };

  return (
    <section className="space-y-5" aria-live="polite">
      <div className="relative overflow-hidden rounded-3xl border border-zinc-200/90 bg-white/92 p-6 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900/82 dark:shadow-glass sm:p-7">
        <div className="relative flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ibm-blue dark:text-blue-300">Analyzing Your Profile</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-zinc-950 dark:text-zinc-50">Agent pipeline in motion</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
              Each specialist agent processes one step before handing context to the next.
            </p>
          </div>
          <span className="inline-flex w-fit rounded-full border border-blue-200/80 bg-blue-50/80 px-4 py-2 text-xs font-semibold text-ibm-blue dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
            {Math.round(progress)}% complete
          </span>
        </div>

        <div className="relative mt-6 h-2 overflow-hidden rounded-full bg-zinc-200/70 dark:bg-zinc-950/70">
          <div className="h-full rounded-full bg-gradient-to-r from-ibm-blue via-blue-400 to-emerald-400 transition-all duration-200 ease-out" style={{ width: `${progress}%` }} />
        </div>

        <div className="relative mt-6 space-y-2">
          {rows.map((row, index) => {
            const active = row.state === 'active';
            const done = row.state === 'done';
            const error = row.state === 'error';

            return (
              <div
                key={row.key}
                className={`group rounded-2xl border px-4 py-4 transition duration-200 ease-out ${
                  active
                    ? 'border-blue-200 bg-blue-50/80 shadow-[0_14px_32px_-24px_rgba(15,98,254,0.62)] dark:border-blue-400/25 dark:bg-blue-400/10'
                    : error
                      ? 'border-rose-200 bg-rose-50/80 dark:border-rose-400/25 dark:bg-rose-400/10'
                      : 'border-zinc-200/70 bg-white/70 dark:border-white/10 dark:bg-zinc-950/50'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm font-semibold ${
                      done
                        ? 'border-emerald-200 bg-emerald-500 text-white dark:border-emerald-400/20'
                        : active
                          ? 'border-blue-200 bg-ibm-blue text-white dark:border-blue-400/20'
                          : error
                            ? 'border-rose-200 bg-rose-500 text-white dark:border-rose-400/20'
                            : 'border-zinc-200 bg-white text-zinc-400 dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-500'
                    }`}
                  >
                    {active ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : done ? <Check className="h-4 w-4" aria-hidden="true" /> : error ? <AlertCircle className="h-4 w-4" aria-hidden="true" /> : <Circle className="h-3.5 w-3.5" aria-hidden="true" />}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">{row.label}</h3>
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">{statusMeta[row.state].label}</span>
                    </div>
                    <p className="mt-1 text-sm leading-6 text-zinc-600 dark:text-zinc-400">{row.description}</p>
                    {active ? (
                      <div className="mt-3 space-y-2" aria-hidden="true">
                        <span className="block h-2 w-3/4 animate-pulse rounded-full bg-blue-200/70 dark:bg-blue-300/20" />
                        <span className="block h-2 w-1/2 animate-pulse rounded-full bg-zinc-200/80 dark:bg-zinc-700/60" />
                      </div>
                    ) : null}
                    {done && row.snippet ? <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">{row.snippet}</p> : null}
                    {error ? (
                      <button
                        type="button"
                        onClick={() => onRetry(index)}
                        className="mt-3 inline-flex min-h-10 items-center gap-2 rounded-full border border-rose-200 bg-white/80 px-4 py-2 text-sm font-semibold text-rose-700 transition duration-200 ease-out hover:bg-rose-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-500 dark:border-rose-400/20 dark:bg-zinc-900/80 dark:text-rose-300"
                      >
                        <RotateCcw className="h-4 w-4" aria-hidden="true" />
                        Retry this step
                      </button>
                    ) : null}
                  </div>

                  {active ? (
                    <button
                      type="button"
                      onClick={() => onSimulateError(index)}
                      className="hidden min-h-10 rounded-full border border-zinc-200/80 bg-white/70 px-3 py-2 text-xs font-semibold text-zinc-500 transition duration-200 ease-out hover:text-zinc-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:border-white/10 dark:bg-zinc-900/80 dark:text-zinc-400 sm:inline-flex"
                    >
                      Simulate error
                    </button>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

export default PipelineProgress;

