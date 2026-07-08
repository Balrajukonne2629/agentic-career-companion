function AmbientBackground() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-zinc-50 dark:bg-zinc-950">
      <div className="absolute -left-32 -top-24 h-[28rem] w-[28rem] rounded-full bg-blue-300/8 blur-3xl dark:bg-blue-500/15" />
      <div className="absolute -right-36 bottom-[-8rem] h-[32rem] w-[32rem] rounded-full bg-teal-300/6 blur-3xl dark:bg-teal-400/10" />
      <div className="absolute right-[18%] top-20 h-80 w-80 rounded-full bg-violet-300/6 blur-3xl dark:bg-violet-500/10" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_14%_8%,rgba(59,130,246,0.06),transparent_34%),radial-gradient(circle_at_88%_82%,rgba(20,184,166,0.05),transparent_34%),linear-gradient(180deg,rgba(250,250,250,0.96),rgba(248,250,252,0.9))] dark:bg-[radial-gradient(circle_at_12%_10%,rgba(59,130,246,0.12),transparent_34%),radial-gradient(circle_at_88%_78%,rgba(20,184,166,0.09),transparent_32%),radial-gradient(circle_at_72%_12%,rgba(139,92,246,0.08),transparent_28%),linear-gradient(180deg,rgba(9,9,11,0.95),rgba(9,9,11,1))]" />
      <div className="absolute inset-0 opacity-[0.018] dark:opacity-[0.045] [background-image:radial-gradient(circle_at_1px_1px,currentColor_1px,transparent_0)] [background-size:22px_22px] text-zinc-950 dark:text-white" />
    </div>
  );
}

export default AmbientBackground;
