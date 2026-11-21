import { ExternalLink, GraduationCap, Mail, ShieldCheck, User } from 'lucide-react';
import { aboutData } from '../data/faqData';
import { GitHubIcon, LinkedInIcon } from './SocialIcons';

/**
 * Responsive About page component
 * @param {{ onNavigate?: (path: string) => void }} props
 */
function AboutPage({ onNavigate }) {
  return (
    <article className="mx-auto w-full max-w-4xl space-y-6 sm:space-y-8 py-2 sm:py-6">
      <header className="space-y-2 sm:space-y-3 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
          <User className="h-3.5 w-3.5" aria-hidden="true" />
          <span>About The Project</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
          About Agentic Career Companion
        </h1>
        <p className="max-w-2xl text-xs sm:text-sm leading-5 sm:leading-6 text-zinc-600 dark:text-zinc-400">
          An autonomous multi-agent career counseling architecture engineered to bridge computer science academic curricula and modern software engineering industry roles.
        </p>
      </header>

      {/* Developer Profile Section */}
      <section className="rounded-3xl border border-zinc-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/80 sm:p-8">
        <div className="flex flex-col items-center sm:items-start sm:flex-row gap-5 sm:gap-6 text-center sm:text-left">
          <div className="flex h-16 w-16 sm:h-20 sm:w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-xl sm:text-2xl font-bold text-white shadow-md">
            BK
          </div>
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Creator &amp; Lead Engineer
            </div>
            <h2 className="text-lg sm:text-xl font-bold text-zinc-950 dark:text-zinc-50">
              {aboutData.author}
            </h2>
            <div className="flex items-center justify-center sm:justify-start gap-2 text-xs sm:text-sm text-zinc-600 dark:text-zinc-400">
              <GraduationCap className="h-4 w-4 shrink-0 text-ibm-blue dark:text-blue-400" aria-hidden="true" />
              <span>{aboutData.college}</span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Developed for the {aboutData.program}
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-2.5 sm:gap-3 border-t border-zinc-200/70 pt-6 dark:border-white/10">
          <a
            href={aboutData.linkedinUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-2.5 text-xs font-semibold text-blue-700 transition duration-200 hover:bg-blue-100 dark:border-blue-400/20 dark:bg-blue-950/40 dark:text-blue-300"
          >
            <LinkedInIcon className="h-4 w-4" />
            <span>LinkedIn Profile</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
          <a
            href={aboutData.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-full border border-zinc-200 bg-zinc-50 px-4 py-2.5 text-xs font-semibold text-zinc-800 transition duration-200 hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
          >
            <GitHubIcon className="h-4 w-4" />
            <span>Project Repository</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
          <a
            href={`mailto:${aboutData.email}`}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-zinc-200 bg-white px-4 py-2.5 text-xs font-semibold text-zinc-700 transition duration-200 hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <Mail className="h-4 w-4" aria-hidden="true" />
            <span>Contact Author</span>
          </a>
        </div>
      </section>

      {/* Engineering Philosophy Section */}
      <section className="space-y-3 sm:space-y-4 rounded-3xl border border-zinc-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/80 sm:p-8">
        <h2 className="text-base sm:text-lg font-semibold text-zinc-950 dark:text-zinc-50">
          Architecture &amp; Design Mission
        </h2>
        <div className="space-y-3 text-xs sm:text-sm leading-5 sm:leading-6 text-zinc-600 dark:text-zinc-300">
          <p>
            Agentic Career Companion was built to eliminate guesswork from technical career planning. Traditional career tools offer static questionnaires that provide high-level, generic job suggestions without analyzing exact technical capabilities or missing prerequisites.
          </p>
          <p>
            By combining IBM watsonx.ai Granite models with five dedicated autonomous agents (Validation, Profile Analysis, Career Matching, Skill Gap Analysis, and Roadmap Generation), the system acts as a personalized mentor that can understand conversational speech, extract academic records, and produce actionable milestone roadmaps.
          </p>
        </div>
      </section>
    </article>
  );
}

export default AboutPage;
