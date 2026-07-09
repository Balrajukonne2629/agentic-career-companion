import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertTriangle,
  Briefcase,
  CheckCircle2,
  Download,
  Gauge,
  Loader2,
  Map,
  RefreshCcw,
  Target,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import SegmentedToggle from './SegmentedToggle';
import PipelineProgress from './PipelineProgress';
import SpeakMode from './SpeakMode';
import WriteMode from './WriteMode';

const careerMatches = [
  { title: 'Full Stack Developer', fit: '92%', detail: 'Strong fit for React, Java, and product-building interests.' },
  { title: 'Frontend Engineer', fit: '88%', detail: 'Best aligned with UI craft, accessibility, and interaction design.' },
  { title: 'Cloud Application Developer', fit: '81%', detail: 'A good stretch path with backend and deployment practice.' },
];

const skillGaps = [
  { skill: 'Backend APIs', level: 72 },
  { skill: 'Databases', level: 64 },
  { skill: 'System Design', level: 48 },
];

const roadmapSteps = [
  'Build two full-stack projects with auth and database storage.',
  'Practice API design, testing, and deployment workflows.',
  'Create a portfolio case study and prepare for interviews.',
];

const reportSections = [
  { id: 'profile', label: 'Profile' },
  { id: 'career', label: 'Career' },
  { id: 'skill-gap', label: 'Skill Gap' },
  { id: 'roadmap', label: 'Roadmap' },
];

function getMatchTone(value) {
  if (value >= 90) {
    return 'border-emerald-200 bg-emerald-50 text-emerald-600 dark:border-emerald-400/25 dark:bg-emerald-400/10 dark:text-emerald-400';
  }

  if (value >= 75) {
    return 'border-blue-200 bg-blue-50 text-blue-600 dark:border-blue-400/25 dark:bg-blue-400/10 dark:text-blue-400';
  }

  return 'border-amber-200 bg-amber-50 text-amber-600 dark:border-amber-400/25 dark:bg-amber-400/10 dark:text-amber-400';
}

function getReadinessTone(value) {
  if (value >= 75) {
    return {
      bar: 'from-emerald-600 to-blue-600 dark:from-emerald-400 dark:to-blue-400',
      text: 'text-emerald-600 dark:text-emerald-400',
    };
  }

  if (value >= 60) {
    return {
      bar: 'from-blue-600 to-blue-500 dark:from-blue-400 dark:to-blue-500',
      text: 'text-blue-600 dark:text-blue-400',
    };
  }

  return {
    bar: 'from-amber-500 to-amber-400 dark:from-amber-400 dark:to-amber-500',
      text: 'text-amber-600 dark:text-amber-400',
  };
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function normaliseCareerMatches(results) {
  const recommendations = asList(results?.recommendations);
  if (!recommendations.length) return careerMatches;

  return recommendations.slice(0, 3).map((item) => ({
    title: item.title || item.career_title || 'Career Match',
    fit: `${item.confidence_percent ?? item.fit_percent ?? item.score ?? 0}%`,
    detail: item.reasoning || item.detail || item.description || 'Recommended based on your profile and stated goals.',
  }));
}

function normaliseProfileSummary(results) {
  const profile = results?.validation?.profile || {};
  const analysis = results?.profileAnalysis || {};
  const skills = asList(profile.skills).slice(0, 2).join(' + ') || 'Skills mapped';

  return [
    profile.year ? `Year ${profile.year}` : 'Profile validated',
    skills,
    profile.career_goal || analysis.score_band || 'Career goal mapped',
  ];
}

function normaliseSkillGaps(results) {
  const skillGap = results?.skillGap;
  const skillsToLearn = asList(skillGap?.skills_to_learn);

  if (!skillsToLearn.length) return skillGaps;

  // Priority fallback scores when backend readiness_score is unavailable
  const priorityDefault = { Critical: 22, Important: 45, Beneficial: 65 };

  // Sort by readiness_score ascending (lowest first = biggest gap at top)
  const sorted = [...skillsToLearn]
    .filter((item) => item.priority !== 'Beneficial')   // show only required gaps
    .sort((a, b) => {
      const scoreA = a.readiness_score ?? priorityDefault[a.priority] ?? 40;
      const scoreB = b.readiness_score ?? priorityDefault[b.priority] ?? 40;
      return scoreA - scoreB;
    });

  return sorted.slice(0, 5).map((item) => ({
    skill: item.skill || item.tool || 'Skill',
    level: item.readiness_score ?? priorityDefault[item.priority] ?? 40,
  }));
}


function normaliseRoadmapSteps(results) {
  const roadmap = results?.roadmap;

  // DEBUG: Roadmap data inspection
  console.group('%c🗺 normaliseRoadmapSteps() — roadmap data inspection', 'color: #FF9800; font-weight: bold;');
  console.log('results.roadmap value:', roadmap);
  console.log('results.roadmap type:', typeof roadmap);
  if (!roadmap) {
    console.warn('⚠️ results.roadmap is null/undefined — will use MOCK data (roadmapSteps)');
  } else {
    console.log('30_day:', roadmap['30_day']);
    console.log('60_day:', roadmap['60_day']);
    console.log('90_day:', roadmap['90_day']);
    const focuses = ['30_day', '60_day', '90_day'].map((k) => ({ phase: k, focus: roadmap[k]?.focus ?? '⚠️ missing' }));
    console.table(focuses);
  }
  console.groupEnd();

  if (!roadmap) return roadmapSteps;

  const steps = ['30_day', '60_day', '90_day']
    .map((key) => roadmap[key]?.focus)
    .filter(Boolean)
    .slice(0, 3);

  if (steps.length === 0) {
    console.warn('⚠️ normaliseRoadmapSteps: roadmap exists but NO focus strings found — will use MOCK data');
    return roadmapSteps;
  }

  console.log('%c✅ normaliseRoadmapSteps: returning real roadmap steps:', 'color:#4CAF50;', steps);
  return steps;
}

function DashboardReport({ reducedMotion, onRetryStep, pipelineResults, roadmapLoading = false }) {
  const [activeSection, setActiveSection] = useState('career');
  const reportCareerMatches = useMemo(() => normaliseCareerMatches(pipelineResults), [pipelineResults]);
  const reportProfileSummary = useMemo(() => normaliseProfileSummary(pipelineResults), [pipelineResults]);
  const reportSkillGaps = useMemo(() => normaliseSkillGaps(pipelineResults), [pipelineResults]);
  const reportRoadmapSteps = useMemo(() => normaliseRoadmapSteps(pipelineResults), [pipelineResults]);
  const topMatch = Number.parseInt(reportCareerMatches[0]?.fit, 10) || 0;
  const readiness =
    pipelineResults?.profileAnalysis?.career_readiness_score ??
    Math.round(reportSkillGaps.reduce((total, item) => total + item.level, 0) / reportSkillGaps.length);

  // Determine Granite status from backend response
  const graniteStatus = pipelineResults?.roadmap?.granite_status; // 'granite' | 'fallback' | undefined
  const roadmapIsFallback = graniteStatus === 'fallback';
  const roadmapIsAvailable = !!pipelineResults?.roadmap && reportRoadmapSteps.length > 0;

  // Status badge config
  const graniteBadge = roadmapLoading
    ? { dot: 'bg-blue-400 animate-pulse', text: 'text-blue-600 dark:text-blue-400', label: 'Generating…' }
    : graniteStatus === 'granite'
      ? { dot: 'bg-emerald-500', text: 'text-emerald-600 dark:text-emerald-400', label: '🟢 Granite Active' }
      : graniteStatus === 'fallback'
        ? { dot: 'bg-amber-400', text: 'text-amber-600 dark:text-amber-400', label: '🟡 Fallback Mode' }
        : { dot: 'bg-rose-500', text: 'text-rose-600 dark:text-rose-400', label: '🔴 Service Unavailable' };

  // DEBUG: Full pipeline results at dashboard render time
  console.group('%c📊 DashboardReport mounted — full pipelineResults inspection', 'color: #2196F3; font-weight: bold; font-size: 14px;');
  console.log('pipelineResults (full object):', pipelineResults);
  console.table([
    { key: 'validation', present: !!pipelineResults?.validation, type: typeof pipelineResults?.validation },
    { key: 'profileAnalysis', present: !!pipelineResults?.profileAnalysis, type: typeof pipelineResults?.profileAnalysis },
    { key: 'recommendations', present: !!pipelineResults?.recommendations, type: typeof pipelineResults?.recommendations, length: pipelineResults?.recommendations?.length },
    { key: 'skillGap', present: !!pipelineResults?.skillGap, type: typeof pipelineResults?.skillGap },
    { key: 'roadmap', present: !!pipelineResults?.roadmap, type: typeof pipelineResults?.roadmap },
  ]);
  console.log('reportRoadmapSteps (what will render):', reportRoadmapSteps);
  if (!pipelineResults?.roadmap) {
    console.warn('⚠️ pipelineResults.roadmap is null/undefined — Roadmap section will show MOCK data');
  }
  console.groupEnd();

  const handleExportReport = () => {
    window.print();
  };

  useEffect(() => {
    if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') return undefined;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (visible?.target?.id) {
          setActiveSection(visible.target.id);
        }
      },
      { rootMargin: '-18% 0px -60% 0px', threshold: [0.15, 0.35, 0.6] },
    );

    reportSections.forEach((section) => {
      const node = document.getElementById(section.id);
      if (node) observer.observe(node);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <motion.section
      key="dashboard"
      initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
      transition={{ duration: 0.18, ease: 'easeOut' }}
      className="space-y-6"
    >
      <header className="rounded-3xl border border-zinc-200/90 bg-white/92 p-6 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900 dark:shadow-glass sm:p-7">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-emerald-600 dark:text-emerald-400">Pipeline Complete</p>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-zinc-950 dark:text-zinc-50 md:text-5xl">Your Career Report</h1>
            <p className="mt-3 max-w-[68ch] text-base leading-7 text-zinc-600 dark:text-zinc-400">
              A focused summary of your strongest career matches, readiness gaps, and first learning path.
            </p>
            <p className="mt-2 text-xs text-zinc-400 dark:text-zinc-500">
              Generated: {new Date().toLocaleString()}
            </p>
          </div>
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-emerald-200/80 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Report Ready
          </span>
        </div>
        <div className="hidden print:flex flex-row gap-8 mt-4 border-t border-zinc-200/60 pt-4 dark:border-zinc-800">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Top Match</p>
            <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{topMatch}%</p>
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Overall Career Readiness Score</p>
            <p className="mt-1 text-2xl font-bold text-blue-600 dark:text-blue-400">{readiness}%</p>
          </div>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[10rem_minmax(0,1fr)_15rem] lg:items-start">
        <aside className="hidden lg:sticky lg:top-16 lg:block">
          <nav aria-label="Career report sections" className="rounded-3xl border border-zinc-200/90 bg-white/82 p-3 shadow-sm backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900">
            {reportSections.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className={`block rounded-2xl px-3 py-2 text-sm font-semibold transition duration-200 ease-out ${
                  activeSection === section.id
                    ? 'bg-blue-600 text-white shadow-sm dark:bg-blue-400 dark:text-zinc-950'
                    : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-950 dark:text-zinc-400 dark:hover:bg-zinc-950/70 dark:hover:text-zinc-50'
                }`}
              >
                {section.label}
              </a>
            ))}
          </nav>
        </aside>

        <div className="print-area min-w-0 space-y-5">
          <section id="career" className="scroll-mt-20 rounded-3xl border border-blue-200 bg-white p-5 shadow-md dark:border-blue-400/30 dark:bg-zinc-900 dark:shadow-glass sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-400/10 dark:text-blue-400">
                  <Briefcase className="h-5 w-5" aria-hidden="true" />
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-600 dark:text-blue-400">Primary Result</p>
                  <h2 className="text-xl font-bold tracking-tight text-zinc-950 dark:text-zinc-50">Career Recommendations</h2>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRetryStep(2)}
                className="inline-flex min-h-10 w-fit items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-600 transition duration-200 ease-out hover:bg-blue-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-400"
              >
                <RefreshCcw className="h-4 w-4" aria-hidden="true" />
                Re-generate
              </button>
            </div>

            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              {reportCareerMatches.map((match, index) => {
                const fitValue = Number.parseInt(match.fit, 10);
                return (
                  <article
                    key={match.title}
                    className={`rounded-3xl border bg-zinc-50 p-5 shadow-sm dark:bg-zinc-950 ${
                      index === 0 ? 'border-blue-200 dark:border-blue-400/30' : 'border-zinc-200 dark:border-zinc-800'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-base font-bold leading-6 text-zinc-950 dark:text-zinc-50">{match.title}</h3>
                      <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${getMatchTone(fitValue)}`}>{match.fit}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-zinc-600 dark:text-zinc-400">{match.detail}</p>
                    {index === 0 ? (
                      <p className="mt-4 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-400">
                        Strongest match
                      </p>
                    ) : null}
                  </article>
                );
              })}
            </div>
          </section>

          <section id="profile" className="scroll-mt-20 rounded-3xl border border-zinc-200/90 bg-white/92 p-5 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900 dark:shadow-glass">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-400/10 dark:text-blue-400">
                  <Gauge className="h-5 w-5" aria-hidden="true" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-zinc-950 dark:text-zinc-50">Profile Summary</h2>
                  <p className="max-w-[65ch] text-sm leading-6 text-zinc-500 dark:text-zinc-400">Validated student context and readiness snapshot.</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRetryStep(1)}
                className="inline-flex min-h-10 w-fit items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-600 transition duration-200 ease-out hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-300"
              >
                <RefreshCcw className="h-4 w-4" aria-hidden="true" />
                Re-run profile
              </button>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-3">
              {reportProfileSummary.map((item) => (
                <div key={item} className="rounded-2xl border border-zinc-200/80 bg-zinc-50/80 px-4 py-3 text-sm font-semibold text-zinc-700 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200">
                  {item}
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-5 md:grid-cols-2">
            <div id="skill-gap" className="scroll-mt-20 rounded-3xl border border-zinc-200/90 bg-white/92 p-5 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900 dark:shadow-glass">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between md:flex-col md:items-start xl:flex-row xl:items-center">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-400/10 dark:text-blue-400">
                    <Target className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <h2 className="text-lg font-bold text-zinc-950 dark:text-zinc-50">Skill Gap</h2>
                </div>
                <button
                  type="button"
                  onClick={() => onRetryStep(3)}
                  className="inline-flex min-h-10 w-fit items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-600 transition duration-200 ease-out hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-300"
                >
                  <RefreshCcw className="h-4 w-4" aria-hidden="true" />
                  Re-check
                </button>
              </div>
              <div className="mt-5 space-y-4">
                {reportSkillGaps.map((gap) => {
                  const tone = getReadinessTone(gap.level);
                  return (
                    <div key={gap.skill}>
                      <div className="mb-2 flex items-center justify-between gap-3 text-xs font-medium text-zinc-500 dark:text-zinc-400">
                        <span>{gap.skill}</span>
                        <span className={tone.text}>{gap.level}% ready</span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-zinc-200/80 dark:bg-zinc-950/70">
                        <div className={`h-full rounded-full bg-gradient-to-r ${tone.bar}`} style={{ width: `${gap.level}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div id="roadmap" className="scroll-mt-20 rounded-3xl border border-zinc-200/90 bg-white/92 p-5 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900 dark:shadow-glass">
              {/* Card header with status badge */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between md:flex-col md:items-start xl:flex-row xl:items-start">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600 dark:bg-blue-400/10 dark:text-blue-400">
                    <Map className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-zinc-950 dark:text-zinc-50">Roadmap Steps</h2>
                    {/* Granite status badge */}
                    <span className={`mt-0.5 flex items-center gap-1.5 text-xs font-semibold ${graniteBadge.text}`}>
                      <span className={`inline-block h-1.5 w-1.5 rounded-full ${graniteBadge.dot}`} />
                      {graniteBadge.label}
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onRetryStep(4)}
                  className="inline-flex min-h-10 w-fit items-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-600 transition duration-200 ease-out hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-300"
                >
                  <RefreshCcw className="h-4 w-4" aria-hidden="true" />
                  Rebuild
                </button>
              </div>

              {/* STATE 1 — Loading */}
              {roadmapLoading ? (
                <div className="mt-6 flex flex-col items-center gap-4 py-8 text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500 dark:text-blue-400" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-semibold text-zinc-700 dark:text-zinc-200">Generating personalized roadmap…</p>
                    <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">Powered by IBM Granite</p>
                  </div>
                </div>
              ) : roadmapIsAvailable ? (
                /* STATE 2 — Success */
                <div className="mt-5 space-y-4">
                  {roadmapIsFallback && (
                    <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                      Generated using fallback planner
                    </p>
                  )}
                  {reportRoadmapSteps.map((step, index) => (
                    <div key={step} className="flex gap-3 text-sm leading-6 text-zinc-600 dark:text-zinc-400">
                      <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-950 text-xs font-semibold text-white dark:bg-white dark:text-zinc-950">{index + 1}</span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              ) : (
                /* STATE 3 — Fallback / Service Unavailable */
                <div className="mt-5 rounded-2xl border border-amber-200/80 bg-amber-50/60 p-5 dark:border-amber-400/20 dark:bg-amber-400/8">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-500 dark:text-amber-400" aria-hidden="true" />
                    <div className="flex-1">
                      <p className="text-sm font-bold text-amber-800 dark:text-amber-300">
                        IBM Granite is currently busy.
                      </p>
                      <p className="mt-1.5 text-sm leading-6 text-amber-700 dark:text-amber-400">
                        Your profile has been successfully analyzed, but roadmap generation is temporarily unavailable. Please try again in a few moments.
                      </p>
                      <button
                        type="button"
                        onClick={() => onRetryStep(4)}
                        className="mt-4 inline-flex min-h-9 items-center gap-2 rounded-full border border-amber-300 bg-white px-4 py-2 text-xs font-semibold text-amber-700 transition duration-200 ease-out hover:bg-amber-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-500 dark:border-amber-400/30 dark:bg-zinc-950 dark:text-amber-400 dark:hover:bg-amber-400/10"
                      >
                        <RefreshCcw className="h-3.5 w-3.5" aria-hidden="true" />
                        Retry Roadmap
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        </div>

        <aside className="hidden lg:sticky lg:top-16 lg:block">
          <div className="rounded-3xl border border-zinc-200/90 bg-white/92 p-5 shadow-md backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-900 dark:shadow-glass">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-500 dark:text-zinc-400">Summary</p>
            <div className="mt-4 space-y-4">
              <div>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Top Match</p>
                <p className="mt-1 text-3xl font-bold text-emerald-600 dark:text-emerald-400">{topMatch}%</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Overall Readiness</p>
                <p className="mt-1 text-3xl font-bold text-blue-600 dark:text-blue-400">{readiness}%</p>
              </div>

              <button
                type="button"
                onClick={handleExportReport}
                className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-2 text-sm font-semibold text-zinc-600 transition duration-200 ease-out hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-300"
              >
                <Download className="h-4 w-4" aria-hidden="true" />
                Export Report
              </button>
            </div>
          </div>
        </aside>
      </div>
    </motion.section>
  );
}

/**
 * @param {{
 *  mode: 'speak' | 'write',
 *  onModeChange: (mode: 'speak' | 'write') => void,
 *  screen: 'compose' | 'pipeline' | 'dashboard',
 *  pipelineRows: Array<{ key: string, label: string, description: string, state: 'idle' | 'active' | 'done' | 'error', snippet: string }>,
 *  pipelineResults: Record<string, unknown>,
 *  onStartPipeline: (payload: string) => void,
 *  onRetryStep: (index: number) => void,
 *  onSimulateError: (index: number) => void,
 *  draft: string,
 *  setDraft: (value: string) => void,
 *  reducedMotion?: boolean,
 * }} props
 */
function WorkspaceCard({
  mode,
  onModeChange,
  screen,
  pipelineRows,
  pipelineResults,
  onStartPipeline,
  onRetryStep,
  onSubmitIncomplete,
  onSimulateError,
  draft,
  setDraft,
  reducedMotion = false,
}) {
  const [speechWarning, setSpeechWarning] = useState(false);

  const handleModeChange = (newMode) => {
    if (newMode === 'speak') {
      const SpeechRecognition = typeof window !== 'undefined' ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
      if (!SpeechRecognition) {
        setSpeechWarning(true);
        onModeChange('write');
        return;
      }
    }
    setSpeechWarning(false);
    onModeChange(newMode);
  };

  useEffect(() => {
    if (mode === 'speak') {
      const SpeechRecognition = typeof window !== 'undefined' ? (window.SpeechRecognition || window.webkitSpeechRecognition) : null;
      if (!SpeechRecognition) {
        setSpeechWarning(true);
        onModeChange('write');
      }
    }
  }, [mode, onModeChange]);

  const pipelinePreview = useMemo(
    () => pipelineRows.map((row) => ({ key: row.key, label: row.label.replace(' Agent', ''), state: row.state })),
    [pipelineRows],
  );


  if (screen === 'dashboard') {
    const roadmapLoading = pipelineRows.some((r) => r.key === 'roadmap' && r.state === 'active');
    return <DashboardReport reducedMotion={reducedMotion} onRetryStep={onRetryStep} pipelineResults={pipelineResults} roadmapLoading={roadmapLoading} />;
  }

  const currentPanel =
    screen === 'pipeline' ? (
      <PipelineProgress rows={pipelineRows} onRetry={onRetryStep} onSimulateError={onSimulateError} onSubmitIncomplete={onSubmitIncomplete} />
    ) : mode === 'speak' ? (
      <SpeakMode onContinue={onStartPipeline} onFallback={() => handleModeChange('write')} reducedMotion={reducedMotion} />
    ) : (
      <WriteMode value={draft} onChange={setDraft} onContinue={onStartPipeline} speechWarning={speechWarning} reducedMotion={reducedMotion} />
    );

  return (
    <section className="space-y-6">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-zinc-500 dark:text-zinc-500">Workspace</p>
        <h1 className="mx-auto mt-3 max-w-2xl text-balance text-3xl font-bold leading-[0.96] tracking-tight text-zinc-950 dark:text-zinc-50 md:text-5xl lg:text-6xl">
          Let's understand you better
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-pretty text-base leading-7 text-zinc-600 dark:text-zinc-300 md:text-lg md:leading-8">
          Share your background and goals - we'll build your personalized career roadmap.
        </p>
      </div>

      {screen === 'compose' ? (
        <SegmentedToggle value={mode} onChange={handleModeChange} reducedMotion={reducedMotion} />
      ) : (
        <div className="flex items-center justify-center gap-2 overflow-x-auto text-xs text-zinc-500 dark:text-zinc-400">
          {pipelinePreview.map((stage, index) => (
            <span key={stage.key} className="inline-flex shrink-0 items-center gap-2">
              <span className={stage.state === 'done' ? 'text-emerald-600 dark:text-emerald-400' : stage.state === 'active' ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-400'}>
                {stage.label}
              </span>
              {index < pipelinePreview.length - 1 ? <span aria-hidden="true">/</span> : null}
            </span>
          ))}
        </div>
      )}

      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={`${screen}-${mode}`}
          initial={reducedMotion ? { opacity: 0 } : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reducedMotion ? { opacity: 0 } : { opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="overflow-hidden"
        >
          {currentPanel}
        </motion.div>
      </AnimatePresence>
    </section>
  );
}

export default WorkspaceCard;




