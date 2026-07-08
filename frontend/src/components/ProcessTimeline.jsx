import { howItWorksStages } from '../data/workspaceCopy';

function ProcessTimeline() {
  return (
    <section className="mx-auto mt-10 max-w-2xl rounded-[2rem] border border-white/80 bg-white/75 p-5 shadow-panel backdrop-blur-xl sm:p-6 lg:p-8">
      <div className="mb-6 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-slate-500">How it works</p>
          <h2 className="mt-2 text-2xl font-semibold text-ibm-ink sm:text-3xl">A minimal path from introduction to roadmap</h2>
        </div>
        <p className="max-w-xl text-sm leading-6 text-slate-600">
          The UI mirrors the actual backend flow while keeping the experience compact and legible.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-3 xl:grid-cols-6">
        {howItWorksStages.map((stage, index) => (
          <div key={stage.title} className="relative rounded-3xl border border-ibm-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#EAF1FF] text-sm font-semibold text-ibm-blue">
                0{index + 1}
              </div>
              {index < howItWorksStages.length - 1 ? (
                <div className="hidden h-px flex-1 bg-gradient-to-r from-ibm-line to-transparent lg:block" />
              ) : null}
            </div>
            <h3 className="text-lg font-semibold text-ibm-ink">{stage.title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{stage.detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default ProcessTimeline;
