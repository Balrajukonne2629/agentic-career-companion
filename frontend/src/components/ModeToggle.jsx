import { modeOptions } from '../data/workspaceCopy';

function ModeToggle({ value, onChange }) {
  return (
    <div className="inline-flex w-full max-w-md rounded-[1.4rem] border border-ibm-line bg-white/90 p-1 shadow-panel backdrop-blur-sm sm:w-auto">
      <div className="relative flex w-full items-center" role="tablist" aria-label="Introduction mode">
        <span
          aria-hidden="true"
          className="absolute inset-y-1 left-1 w-[calc(50%-0.25rem)] rounded-[1.1rem] bg-ibm-blue shadow-glow transition-transform duration-300 ease-out"
          style={{ transform: value === 'write' ? 'translateX(100%)' : 'translateX(0%)' }}
        />
        {modeOptions.map((option) => {
          const active = value === option.key;
          return (
            <button
              key={option.key}
              type="button"
              onClick={() => onChange(option.key)}
              aria-pressed={active}
              aria-label={`${option.label} mode`}
              className={`relative z-10 flex-1 rounded-[1.1rem] px-4 py-3 text-sm font-semibold transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue sm:px-6 ${
                active ? 'text-white' : 'text-ibm-text hover:bg-slate-50 hover:text-ibm-blue'
              }`}
            >
              <span className="mr-2 text-base">{option.icon}</span>
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ModeToggle;