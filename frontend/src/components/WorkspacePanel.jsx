import {
  loadingStages,
  pipelinePreviewSteps,
  speakChecklist,
  speakDuration,
  speakExample,
  transcriptPreview,
  writePlaceholder,
  writeSuggestion,
} from '../data/workspaceCopy';
import { useMemo, useState } from 'react';

function ActionButton({ children, tone = 'primary', type = 'button', onClick, ariaLabel }) {
  const variants = {
    primary:
      'bg-ibm-blue text-white shadow-glow hover:bg-ibm-blueDeep focus-visible:outline-ibm-blue',
    secondary:
      'border border-ibm-line bg-white text-ibm-text hover:border-ibm-blue hover:text-ibm-blue',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      aria-label={ariaLabel}
      className={`inline-flex items-center justify-center rounded-full px-5 py-3 text-sm font-semibold transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${variants[tone]}`}
    >
      {children}
    </button>
  );
}

function MicrophoneIllustration() {
  return (
    <div className="relative mx-auto flex h-52 w-full max-w-sm items-center justify-center overflow-hidden rounded-[2rem] border border-white/70 bg-gradient-to-br from-[#F0F6FF] via-white to-[#E8F0FF] shadow-panel">
      <div className="absolute inset-6 rounded-[1.75rem] border border-white/70 bg-white/50" />
      <div className="absolute h-28 w-28 rounded-full bg-ibm-blue/10 blur-2xl animate-pulseSoft" />
      <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-ibm-blue/20 bg-white shadow-glow">
        <svg viewBox="0 0 120 120" className="h-16 w-16 text-ibm-blue" fill="none" aria-hidden="true">
          <rect x="44" y="20" width="32" height="48" rx="16" stroke="currentColor" strokeWidth="8" />
          <path d="M32 54c0 15.46 12.54 28 28 28s28-12.54 28-28" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
          <path d="M60 82v18" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
          <path d="M44 100h32" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
        </svg>
      </div>
    </div>
  );
}

function PreviewCard({ title, children, className = '' }) {
  return (
    <div className={`rounded-2xl border border-ibm-line bg-white/90 p-4 shadow-sm ${className}`}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{title}</p>
      {children}
    </div>
  );
}

function LoadingPreview() {
  return (
    <div className="rounded-3xl border border-ibm-line bg-white/95 p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-ibm-blue">Analyzing Your Profile</p>
          <p className="mt-1 text-sm text-slate-600">A visual preview of the agent pipeline. No backend call is made here.</p>
        </div>
        <div className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
          AI Ready
        </div>
      </div>

      <div className="mt-5 space-y-3">
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full w-[62%] rounded-full bg-gradient-to-r from-ibm-blue via-[#4A8BFF] to-ibm-blueDeep transition-all duration-500" />
        </div>
        <div className="grid gap-2">
          {loadingStages.map((stage) => (
            <div key={stage.label} className="flex items-center gap-3 rounded-2xl border border-ibm-line bg-slate-50/80 px-4 py-3">
              <span
                className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                  stage.state === 'done'
                    ? 'bg-emerald-500 text-white'
                    : stage.state === 'active'
                      ? 'bg-ibm-blue text-white'
                      : 'border border-slate-300 bg-white text-slate-400'
                }`}
              >
                {stage.state === 'done' ? '✓' : stage.state === 'active' ? '●' : '○'}
              </span>
              <span className="text-sm text-slate-700">{stage.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function PipelinePreview() {
  return (
    <div className="rounded-3xl border border-ibm-line bg-white/90 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">AI Pipeline</p>
      <div className="mt-4 space-y-3">
        {pipelinePreviewSteps.map((stage, index) => (
          <div key={stage}>
            <div className="flex items-center gap-3 rounded-2xl border border-ibm-line bg-[#FBFCFF] px-4 py-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#EAF1FF] text-sm font-semibold text-ibm-blue">
                0{index + 1}
              </span>
              <span className="text-sm font-medium text-ibm-ink">{stage}</span>
            </div>
            {index < pipelinePreviewSteps.length - 1 ? (
              <div className="my-2 flex justify-center text-ibm-blue/60">↓</div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function SpeakWorkspace({ onContinue }) {
  const [hasRecorded, setHasRecorded] = useState(false);

  const onboardingChecklist = useMemo(
    () => speakChecklist.map((item) => `✓ ${item}`),
    [],
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-5">
        {!hasRecorded ? (
          <div className="space-y-5 rounded-[2rem] border border-ibm-line bg-white/95 p-6 shadow-panel">
            <div className="flex items-center justify-between gap-4">
              <div className="rounded-2xl bg-[#EAF1FF] p-3 text-2xl">🎤</div>
              <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                {speakDuration}
              </span>
            </div>

            <div className="space-y-3">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Ready to introduce yourself?</p>
              <h3 className="text-2xl font-semibold text-ibm-ink">Help us understand your profile.</h3>
              <p className="text-sm leading-7 text-slate-600">
                Mention things like your current year, skills, interests, CGPA, and career goal. The experience is designed to feel calm and guided before any recording begins.
              </p>
            </div>

            <div className="grid gap-2 rounded-3xl border border-ibm-line bg-[#FBFCFF] p-4 sm:grid-cols-2">
              {onboardingChecklist.map((item) => (
                <div key={item} className="flex items-center gap-2 rounded-2xl bg-white px-3 py-2 text-sm text-slate-700 shadow-sm">
                  <span className="text-ibm-blue">{item}</span>
                </div>
              ))}
            </div>

            <ActionButton
              ariaLabel="Start recording introduction"
              onClick={() => setHasRecorded(true)}
              tone="primary"
            >
              Start Recording
            </ActionButton>
          </div>
        ) : (
          <div className="space-y-5 rounded-[2rem] border border-ibm-line bg-white/95 p-6 shadow-panel animate-fadeUp">
            <div className="flex items-center justify-between gap-4">
              <div className="rounded-2xl bg-[#EAF1FF] p-3 text-2xl">📝</div>
              <span className="rounded-full border border-ibm-line bg-white px-3 py-1 text-xs font-semibold text-slate-600">
                Transcript ready
              </span>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold text-ibm-blue">Review before continuing</p>
              <p className="text-sm leading-6 text-slate-600">
                This preview represents the captured transcript. The student always reviews it before moving to the next step.
              </p>
            </div>
            <PreviewCard title="Live transcript preview" className="min-h-56">
              <p className="whitespace-pre-wrap font-mono text-sm leading-6 text-slate-700">
                {transcriptPreview}
              </p>
            </PreviewCard>

            <div className="grid gap-3 sm:grid-cols-2">
              <ActionButton tone="secondary" ariaLabel="Edit transcript">
                Edit Transcript
              </ActionButton>
              <ActionButton tone="primary" ariaLabel="Continue with transcript" onClick={onContinue}>
                Continue
              </ActionButton>
            </div>
          </div>
        )}

        <div className="space-y-3 rounded-3xl border border-ibm-line bg-white/90 p-5 shadow-sm">
          <p className="text-sm font-semibold text-ibm-blue">Example introduction</p>
          <p className="text-sm leading-6 text-slate-600">A useful reference if you prefer to speak less formally.</p>
          <PreviewCard title="Suggested flow">
            <p className="whitespace-pre-wrap rounded-2xl bg-[#F7FAFF] p-4 text-sm leading-6 text-slate-700">
              {speakExample}
            </p>
          </PreviewCard>
        </div>
      </div>

      <div className="space-y-4">
        <LoadingPreview />
        <PipelinePreview />
        <div className="rounded-3xl border border-ibm-line bg-white/90 p-5 shadow-sm">
          <p className="text-sm font-semibold text-ibm-blue">What happens next</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            After review, the profile enters the backend pipeline: validation, profile analysis, career recommendation, skill gap analysis, and roadmap generation.
          </p>
        </div>
      </div>
    </div>
  );
}

function WriteWorkspace({ draft, setDraft }) {
  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-4 rounded-[2rem] border border-ibm-line bg-white/95 p-6 shadow-panel">
        <div>
          <p className="text-sm font-semibold text-ibm-blue">Write mode</p>
          <h3 className="mt-1 text-2xl font-semibold text-ibm-ink">Type your introduction directly into the workspace</h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Keep it natural, but make sure the core details are easy to spot for the validation agent.
          </p>
        </div>

        <div className="rounded-[1.75rem] border border-dashed border-ibm-line bg-[#FBFCFE] p-4 shadow-inner">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={writePlaceholder}
            aria-label="Student introduction text area"
            className="min-h-80 w-full resize-none bg-transparent text-base leading-7 text-slate-800 outline-none placeholder:text-slate-400 focus-visible:outline-none"
          />
        </div>

        <div className="flex items-center justify-between gap-3 text-sm text-slate-500">
          <span>Use 2 to 4 sentences for the strongest profile extraction.</span>
          <span className="font-mono text-xs tracking-wide">{draft.length} characters</span>
        </div>
      </div>

      <div className="space-y-4 rounded-[2rem] border border-ibm-line bg-white/90 p-6 shadow-sm">
        <div className="rounded-[1.75rem] bg-gradient-to-br from-[#F0F6FF] via-white to-[#EEF4FF] p-6">
          <div className="mb-4 inline-flex rounded-full border border-ibm-blue/20 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-ibm-blue">
            Example structure
          </div>
          <p className="text-lg font-semibold text-ibm-ink">Clear, specific, and easy for the validation agent to parse.</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Mention your study program, current year, skills, interests, career goal, and available study time when possible.
          </p>
        </div>

        <PreviewCard title="Helpful prompt">
          <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">{writeSuggestion}</p>
        </PreviewCard>

        <div className="grid gap-3 sm:grid-cols-2">
          <ActionButton tone="secondary" ariaLabel="Clear introduction draft">Clear draft</ActionButton>
          <ActionButton ariaLabel="Continue with written introduction">Continue</ActionButton>
        </div>
        <p className="text-sm leading-6 text-slate-500">
          The draft remains editable so the student can refine the introduction before the next step.
        </p>
      </div>
    </div>
  );
}

function WorkspacePanel({ mode, draft, setDraft }) {
  const handleContinue = () => {};

  return (
    <section
      key={mode}
      className="w-full rounded-[2rem] border border-white/70 bg-white/80 p-4 shadow-panel backdrop-blur-xl sm:p-6 lg:p-7"
      aria-labelledby="workspace-heading"
    >
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <p id="workspace-heading" className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Interactive AI Workspace
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-ibm-ink">Refine your introduction in one focused space</h2>
        </div>
        <div className="hidden rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 sm:inline-flex">
          AI Ready
        </div>
      </div>

      <div className="animate-fadeUp">
        {mode === 'speak' ? (
          <SpeakWorkspace onContinue={handleContinue} />
        ) : (
          <WriteWorkspace draft={draft} setDraft={setDraft} />
        )}
      </div>
    </section>
  );
}

export default WorkspacePanel;