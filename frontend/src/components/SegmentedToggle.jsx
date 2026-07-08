import { motion } from 'framer-motion';
import { Mic, PenLine } from 'lucide-react';
import { modeOptions } from '../data/workspaceCopy';

const ICONS = {
  Mic,
  PenLine,
};

/**
 * @param {{ value: 'speak' | 'write', onChange: (value: 'speak' | 'write') => void, reducedMotion?: boolean }} props
 */
function SegmentedToggle({ value, onChange, reducedMotion = false }) {
  const handleKeyDown = (event) => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') {
      return;
    }

    event.preventDefault();
    const direction = event.key === 'ArrowRight' ? 1 : -1;
    const currentIndex = modeOptions.findIndex((option) => option.key === value);
    const nextIndex = (currentIndex + direction + modeOptions.length) % modeOptions.length;
    onChange(modeOptions[nextIndex].key);
  };

  return (
    <div
      className="relative grid w-full grid-cols-2 rounded-full border border-white/80 bg-white/58 p-1.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72),0_18px_45px_-32px_rgba(15,23,42,0.45)] backdrop-blur-xl dark:border-white/10 dark:bg-white/10"
      role="tablist"
      aria-label="Introduction mode"
      onKeyDown={handleKeyDown}
    >
      {modeOptions.map((option) => {
        const Icon = ICONS[option.icon];
        const active = value === option.key;

        return (
          <button
            key={option.key}
            type="button"
            role="tab"
            aria-selected={active}
            aria-controls={`${option.key}-panel`}
            id={`${option.key}-tab`}
            tabIndex={active ? 0 : -1}
            onClick={() => onChange(option.key)}
            className={`relative min-h-[4.5rem] rounded-full px-4 py-3 text-left transition-colors duration-200 ease-out focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue sm:px-5 ${
              active ? 'text-white dark:text-zinc-950' : 'text-zinc-600 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-zinc-100'
            }`}
          >
            {active && !reducedMotion ? (
              <motion.span
                layoutId="mode-pill"
                className="absolute inset-0 rounded-full bg-zinc-950 shadow-[0_18px_42px_-22px_rgba(15,98,254,0.58)] dark:bg-white"
                transition={{ duration: 0.2, ease: 'easeOut' }}
              />
            ) : active ? (
              <span className="absolute inset-0 rounded-full bg-zinc-950 shadow-glow dark:bg-white" />
            ) : null}

            <span className="relative z-10 flex items-center gap-3">
              <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${active ? 'bg-white/15 dark:bg-zinc-950/10' : 'bg-white/80 dark:bg-white/10'}`}>
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="min-w-0">
                <span className="block text-base font-semibold tracking-tight">{option.label}</span>
                <span className={`mt-0.5 block text-xs font-medium sm:text-sm ${active ? 'text-white/75 dark:text-zinc-700' : 'text-zinc-500 dark:text-zinc-500'}`}>
                  {option.subtitle}
                </span>
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default SegmentedToggle;
