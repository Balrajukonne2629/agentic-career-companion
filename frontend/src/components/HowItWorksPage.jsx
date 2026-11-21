import { Cpu, CheckCircle2, ShieldCheck, ArrowRight, Sparkles, Layers } from 'lucide-react';
import { howItWorksStages } from '../data/workspaceCopy';

/**
 * @param {{ onNavigate?: (path: string) => void }} props
 */
function HowItWorksPage({ onNavigate }) {
  return (
    <article className="mx-auto w-full max-w-4xl space-y-8 py-4 sm:py-6">
      <header className="space-y-3 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
          <Layers className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Multi-Agent System Pipeline</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
          How the Agent Pipeline Works
        </h1>
        <p className="max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
          Discover how 5 specialized AI agents cooperate through an orchestrated pipeline on IBM watsonx.ai to transform your student background into an actionable career roadmap.
        </p>
      </header>

      {/* 5 Agent Cards */}
      <section className="space-y-4" aria-label="Pipeline Stages">
        {howItWorksStages.map((stage, index) => (
          <div
            key={stage.key}
            className="rounded-3xl border border-zinc-200/80 bg-white/80 p-6 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/80"
          >
            <div className="flex items-start gap-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-zinc-950 text-sm font-bold text-white shadow dark:bg-white dark:text-zinc-950">
                0{index + 1}
              </span>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-bold text-zinc-950 dark:text-zinc-50">
                    {stage.title}
                  </h2>
                  <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-ibm-blue dark:bg-blue-950/40 dark:text-blue-300">
                    Agent {index + 1}
                  </span>
                </div>
                <p className="text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                  {stage.detail}
                </p>
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* Fallback & Reliability Section */}
      <section className="rounded-3xl border border-zinc-200/80 bg-white/80 p-6 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/80 sm:p-8">
        <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
          <ShieldCheck className="h-5 w-5" aria-hidden="true" />
          <h2 className="text-base font-bold uppercase tracking-wider text-zinc-950 dark:text-zinc-50">
            Fault-Tolerant Fallback Architecture
          </h2>
        </div>
        <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-300">
          The pipeline features an automatic dual-layer architecture. If IBM watsonx.ai experiences rate-limiting (HTTP 429) or temporary outages, the system automatically degrades gracefully to pure Python extraction and deterministic local heuristics. Your career evaluation proceeds without interruptions or lost state.
        </p>
      </section>

      {/* CTA */}
      <aside className="rounded-3xl border border-blue-200/80 bg-blue-50/50 p-6 text-center dark:border-blue-400/20 dark:bg-blue-950/20 sm:p-8">
        <Sparkles className="mx-auto h-6 w-6 text-ibm-blue dark:text-blue-400" aria-hidden="true" />
        <h3 className="mt-2 text-lg font-semibold text-zinc-950 dark:text-zinc-50">
          Experience the 5-Agent Pipeline Live
        </h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-zinc-600 dark:text-zinc-400">
          Start your counseling session now by speaking or writing your academic profile.
        </p>
        <button
          type="button"
          onClick={() => onNavigate && onNavigate('/')}
          className="mt-4 inline-flex items-center justify-center gap-2 rounded-full bg-ibm-blue px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-200 hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue"
        >
          <span>Launch AI Companion</span>
          <ArrowRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </aside>
    </article>
  );
}

export default HowItWorksPage;
