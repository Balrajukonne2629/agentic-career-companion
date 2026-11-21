import {
  BrainCircuit,
  ExternalLink,
  GraduationCap,
  Layers,
  Sparkles,
  Users,
  ShieldCheck,
} from 'lucide-react';
import { aboutData } from '../data/faqData';

/**
 * Static SEO/AEO content for the landing page with fully responsive styling.
 * Adheres strictly to SEO requirements:
 * - Exactly one <h1> "AI Career Counseling Companion"
 * - Directly under it, the 2-sentence plain definition
 * - 300+ words of real static content detailing what it does, the 5 agents, and who it is for
 * - Embedded /about section with author name, college, GitHub and LinkedIn links
 * - Semantic HTML tags with descriptive accessibility attributes
 */
function LandingSEOContent({ onNavigate }) {
  return (
    <article className="mt-8 w-full space-y-8 border-t border-zinc-200/70 pt-8 sm:mt-12 sm:space-y-12 sm:pt-12 dark:border-white/10">
      {/* Primary Semantic Header with H1 and 2-sentence plain definition */}
      <header className="space-y-3 sm:space-y-4 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
          <span>IBM watsonx.ai &amp; Granite Powered</span>
        </div>

        <h1 className="text-2xl font-extrabold tracking-tight text-zinc-950 sm:text-4xl lg:text-5xl dark:text-zinc-50">
          AI Career Counseling Companion
        </h1>

        <p className="mx-auto max-w-3xl text-sm font-normal leading-6 text-zinc-700 sm:mx-0 sm:text-base sm:leading-7 dark:text-zinc-300">
          Agentic Career Companion is a multi-agent AI career counseling tool built on IBM watsonx.ai. It analyzes your skills, finds career matches, identifies skill gaps and generates a personalized learning roadmap.
        </p>
      </header>

      {/* Section 1: What It Does (Semantic <section>) */}
      <section className="rounded-3xl border border-zinc-200/80 bg-white/70 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/60 sm:p-8">
        <div className="flex items-center gap-2.5 text-ibm-blue dark:text-blue-400">
          <BrainCircuit className="h-5 w-5 shrink-0" aria-hidden="true" />
          <h2 className="text-lg font-bold tracking-tight text-zinc-950 sm:text-xl dark:text-zinc-50">
            What It Does
          </h2>
        </div>
        <div className="mt-3 space-y-3 text-xs leading-5 text-zinc-600 sm:mt-4 sm:space-y-4 sm:text-sm sm:leading-7 dark:text-zinc-300">
          <p>
            Agentic Career Companion transforms the traditional, fragmented student career counseling experience into an autonomous, data-driven journey. Many computer science and engineering students struggle to translate academic coursework into tangible industry readiness. This platform provides an intelligent, conversational interface where students can either speak naturally or write their academic backgrounds, technical competencies, personal projects, and career aspirations.
          </p>
          <p>
            The platform analyzes spoken or typed student introductions, evaluates engineering proficiencies against comprehensive industry benchmarks, and constructs a tailored 30, 60, and 90-day learning curriculum. The entire workflow gives students actionable clarity on exactly where they stand today and what concrete steps they need to take to secure their dream software engineering roles.
          </p>
        </div>
      </section>

      {/* Section 2: How the 5 Specialized Agents Work */}
      <section className="rounded-3xl border border-zinc-200/80 bg-white/70 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/60 sm:p-8">
        <div className="flex items-center gap-2.5 text-ibm-blue dark:text-blue-400">
          <Layers className="h-5 w-5 shrink-0" aria-hidden="true" />
          <h2 className="text-lg font-bold tracking-tight text-zinc-950 sm:text-xl dark:text-zinc-50">
            How the 5 Specialized Agents Work
          </h2>
        </div>
        <p className="mt-2 text-xs leading-5 text-zinc-600 sm:text-sm sm:leading-6 dark:text-zinc-400">
          The counseling engine orchestrates five specialized agents combining IBM watsonx.ai Granite foundation models with deterministic Python logic. The Validation, Profile, Career Recommendation, and Roadmap agents leverage Granite for natural language understanding and personalized synthesis, while the Skill Gap Agent runs entirely as deterministic Python set-difference algorithms for mathematical precision, complemented by Python scoring and validation rules across every stage:
        </p>

        <div className="mt-5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 sm:gap-4">
          <div className="rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ibm-blue dark:text-blue-300">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ibm-blue text-[10px] text-white">1</span>
              Validation Agent
            </div>
            <h3 className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">Profile Extraction &amp; Verification</h3>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Extracts profile parameters from spoken or typed introductions using IBM watsonx.ai Granite, followed by deterministic Python normalization and validation checks.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ibm-blue dark:text-blue-300">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ibm-blue text-[10px] text-white">2</span>
              Profile Agent
            </div>
            <h3 className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">Readiness &amp; Tier Analysis</h3>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Generates narrative summaries and strengths with IBM watsonx.ai Granite, while computing readiness scores (0 to 100) and tiers via deterministic Python formulas.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ibm-blue dark:text-blue-300">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ibm-blue text-[10px] text-white">3</span>
              Career Recommendation Agent
            </div>
            <h3 className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">Deterministic Path Matching</h3>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Scores and ranks career matches using deterministic Python overlap algorithms and difficulty penalties, generating tailored match reasoning with Granite.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ibm-blue dark:text-blue-300">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ibm-blue text-[10px] text-white">4</span>
              Skill Gap Agent
            </div>
            <h3 className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">Set-Difference Gap Mining</h3>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Operates entirely on deterministic Python logic, computing exact mathematical set-differences to identify missing required skills, nice-to-haves, and core tools without LLM hallucinations.
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40 sm:col-span-2 lg:col-span-2">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-ibm-blue dark:text-blue-300">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-ibm-blue text-[10px] text-white">5</span>
              Roadmap Agent
            </div>
            <h3 className="mt-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">30/60/90-Day Actionable Curriculum</h3>
            <p className="mt-1 text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Synthesizes milestone 30/60/90-day learning curricula with IBM watsonx.ai Granite, paired with deterministic Python selection of verified industry certifications and projects.
            </p>
          </div>
        </div>
      </section>

      {/* Section 3: Who It Is For */}
      <section className="rounded-3xl border border-zinc-200/80 bg-white/70 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/60 sm:p-8">
        <div className="flex items-center gap-2.5 text-ibm-blue dark:text-blue-400">
          <Users className="h-5 w-5 shrink-0" aria-hidden="true" />
          <h2 className="text-lg font-bold tracking-tight text-zinc-950 sm:text-xl dark:text-zinc-50">
            Who It Is For
          </h2>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-3 sm:gap-4">
          <div className="space-y-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Undergraduate Students</h3>
            <p className="text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Engineering students in 1st through 4th year wanting clear direction on whether to focus on Full Stack, DevOps, Cloud, or AI tracks.
            </p>
          </div>
          <div className="space-y-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Placement Aspirants</h3>
            <p className="text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Graduating engineers needing rapid diagnostic assessment to identify missing technical proficiencies before campus placement interviews.
            </p>
          </div>
          <div className="space-y-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/70 p-4 dark:border-white/5 dark:bg-zinc-950/40">
            <h3 className="text-sm font-semibold text-zinc-950 dark:text-zinc-50">Self-Taught Developers</h3>
            <p className="text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              Learners and career transitioners looking for an objective, benchmarked curriculum instead of overwhelming, unstructured online tutorials.
            </p>
          </div>
        </div>
      </section>

      {/* Section 4: About Section (Author, College, GitHub, LinkedIn) */}
      <section
        id="about"
        className="rounded-3xl border border-zinc-200/80 bg-white/70 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/60 sm:p-8"
      >
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span>Project Author &amp; Creator</span>
            </div>
            <h2 className="text-lg font-bold tracking-tight text-zinc-950 sm:text-xl dark:text-zinc-50">
              {aboutData.author}
            </h2>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              <GraduationCap className="h-4 w-4 shrink-0 text-ibm-blue dark:text-blue-400" aria-hidden="true" />
              <span>{aboutData.college}</span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Developed as part of the {aboutData.program}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
            <a
              href={aboutData.linkedinUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3.5 py-2 text-xs font-semibold text-blue-700 transition duration-200 hover:bg-blue-100 dark:border-blue-400/20 dark:bg-blue-950/40 dark:text-blue-300"
            >
              <span>LinkedIn</span>
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
            <a
              href={aboutData.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-zinc-50 px-3.5 py-2 text-xs font-semibold text-zinc-800 transition duration-200 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
            >
              <span>GitHub</span>
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
            <a
              href="/faq"
              onClick={(e) => {
                e.preventDefault();
                if (onNavigate) {
                  onNavigate('/faq');
                }
              }}
              className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3.5 py-2 text-xs font-semibold text-zinc-700 transition duration-200 hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300"
            >
              <span>View FAQ</span>
            </a>
          </div>
        </div>
      </section>
    </article>
  );
}

export default LandingSEOContent;
