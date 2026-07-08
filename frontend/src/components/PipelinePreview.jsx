/**
 * @param {{ stages: Array<{ key: string, label: string, state: 'idle' | 'active' | 'done' | 'error' }> }} props
 */
function PipelinePreview({ stages }) {
  const stateClasses = {
    idle: 'bg-zinc-300 dark:bg-zinc-700',
    active: 'bg-ibm-blue shadow-[0_0_18px_rgba(15,98,254,0.42)]',
    done: 'bg-emerald-500',
    error: 'bg-rose-500',
  };

  return (
    <section className="rounded-3xl border border-zinc-200/90 bg-white/80 px-4 py-4 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-950/50">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500 dark:text-zinc-400">Pipeline Preview</p>
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-medium text-zinc-500 dark:text-zinc-400 sm:justify-end sm:pb-0">
          {stages.map((stage, index) => (
            <div key={stage.key} className="flex shrink-0 items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${stateClasses[stage.state]}`} aria-hidden="true" />
              <span>{stage.label}</span>
              {index < stages.length - 1 ? <span className="text-zinc-300 dark:text-zinc-700" aria-hidden="true">-&gt;</span> : null}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default PipelinePreview;


