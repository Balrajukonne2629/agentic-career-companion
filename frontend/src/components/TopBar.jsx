import { AnimatePresence, motion } from 'framer-motion';
import { BrainCircuit, CheckCircle2, Info, LockKeyhole, Moon, ShieldCheck, Sparkles, Sun, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { howItWorksStages, projectName, projectSubtitle, topBarBadge } from '../data/workspaceCopy';

/**
 * @param {{ theme: 'light' | 'dark', onToggleTheme: () => void }} props
 */
function TopBar({ theme, onToggleTheme }) {
  const [infoOpen, setInfoOpen] = useState(false);

  useEffect(() => {
    if (!infoOpen || typeof window === 'undefined') return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setInfoOpen(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [infoOpen]);

  return (
    <>
      <header className="sticky top-0 z-50 bg-white/55 backdrop-blur-2xl dark:bg-zinc-950/55">
        <div className="mx-auto flex h-12 max-w-5xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-zinc-950 text-white shadow-sm dark:bg-white dark:text-zinc-950">
              <BrainCircuit className="h-4 w-4" aria-hidden="true" />
            </div>
            <p className="truncate text-sm font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">{projectName}</p>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={onToggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-600 transition duration-200 ease-out hover:bg-zinc-950/5 hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:text-zinc-300 dark:hover:bg-white/10 dark:hover:text-zinc-50"
            >
              {theme === 'dark' ? <Moon className="h-4 w-4" aria-hidden="true" /> : <Sun className="h-4 w-4" aria-hidden="true" />}
            </button>
            <button
              type="button"
              onClick={() => setInfoOpen(true)}
              aria-haspopup="dialog"
              aria-expanded={infoOpen}
              aria-controls="project-info-drawer"
              aria-label="Open project info"
              className="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-600 transition duration-200 ease-out hover:bg-zinc-950/5 hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:text-zinc-300 dark:hover:bg-white/10 dark:hover:text-zinc-50"
            >
              <Info className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {infoOpen ? (
          <>
            <motion.div
              className="fixed inset-0 z-[60] bg-zinc-950/24 backdrop-blur-sm dark:bg-zinc-950/55"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onClick={() => setInfoOpen(false)}
            />
            <motion.aside
              id="project-info-drawer"
              role="dialog"
              aria-modal="true"
              aria-labelledby="project-info-title"
              className="fixed inset-y-0 right-0 z-[61] flex w-full max-w-md flex-col border-l border-zinc-200/70 bg-white/92 shadow-float backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-950/92 sm:w-[26rem]"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
            >
              <div className="flex items-center justify-between gap-3 px-5 py-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-ibm-blue dark:text-blue-300">Project Info</p>
                  <h2 id="project-info-title" className="mt-1 text-lg font-semibold tracking-tight text-zinc-950 dark:text-zinc-50">
                    Workspace details
                  </h2>
                </div>
                <button
                  type="button"
                  onClick={() => setInfoOpen(false)}
                  aria-label="Close project info"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-500 transition duration-200 ease-out hover:bg-zinc-950/5 hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:text-zinc-400 dark:hover:bg-white/10 dark:hover:text-zinc-50"
                >
                  <X className="h-4 w-4" aria-hidden="true" />
                </button>
              </div>

              <div className="flex-1 space-y-5 overflow-y-auto px-5 pb-6">
                <div className="space-y-3 rounded-3xl border border-zinc-200/80 bg-zinc-50/80 p-4 dark:border-white/10 dark:bg-zinc-950/50">
                  <span className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-white px-3 py-2 text-xs font-semibold text-zinc-700 shadow-sm dark:border-blue-400/20 dark:bg-zinc-900/80 dark:text-zinc-200">
                    <Sparkles className="h-3.5 w-3.5 text-ibm-blue dark:text-blue-300" aria-hidden="true" />
                    {topBarBadge}
                  </span>
                  <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-300">
                    <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                    AI Ready
                  </span>
                </div>

                <section className="rounded-3xl border border-zinc-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-zinc-950/50">
                  <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">About Project</h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">{projectSubtitle}</p>
                </section>

                <section>
                  <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">How it works</h3>
                  <div className="mt-3 space-y-3">
                    {howItWorksStages.map((stage, index) => (
                      <div key={stage.key} className="flex gap-3 rounded-2xl border border-zinc-200/80 bg-white/70 p-3 dark:border-white/10 dark:bg-zinc-950/50">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-950 text-xs font-semibold text-white dark:bg-white dark:text-zinc-950">
                          {index + 1}
                        </span>
                        <div>
                          <h4 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">{stage.title}</h4>
                          <p className="mt-1 text-sm leading-5 text-zinc-600 dark:text-zinc-400">{stage.detail}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-3xl border border-zinc-200/80 bg-white/70 p-4 dark:border-white/10 dark:bg-zinc-950/50">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-zinc-950 dark:text-zinc-50">
                    <ShieldCheck className="h-4 w-4 text-emerald-500" aria-hidden="true" />
                    Trust and privacy
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                    Your introduction is reviewed before analysis starts and is used only to generate the career roadmap experience.
                  </p>
                  <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-zinc-100 px-3 py-2 text-xs font-medium text-zinc-500 dark:bg-zinc-900/80 dark:text-zinc-400">
                    <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
                    Privacy mindful student workspace
                  </p>
                </section>
              </div>
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>
    </>
  );
}

export default TopBar;


