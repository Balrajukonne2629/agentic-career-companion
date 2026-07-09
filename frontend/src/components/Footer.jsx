import { Sparkles } from 'lucide-react';
import { projectName, topBarBadge } from '../data/workspaceCopy';

function Footer() {
  return (
    <footer className="relative z-10 border-t border-zinc-200 py-3 text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
      <div className="mx-auto w-full max-w-6xl px-3 sm:px-6 lg:px-0">
        <div className="grid gap-6 md:grid-cols-3 md:items-center md:gap-4">
          <div className="space-y-0.5 text-left leading-tight">
            <p className="font-semibold text-zinc-700 dark:text-zinc-200">{projectName}</p>
            <p className="leading-5">Personalized AI career guidance for students.</p>
          </div>

          <div className="flex flex-col items-start gap-1 md:items-center">
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600 dark:border-blue-400/25 dark:bg-blue-400/10 dark:text-blue-400">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              {topBarBadge}
            </span>
            <p className="text-xs leading-4 text-zinc-400 dark:text-zinc-500">&copy; 2026 Balraju Konne</p>
          </div>

          <div className="space-y-0.5 text-left leading-tight md:text-right">
            <a
              href="mailto:balrajukonne@gmail.com?subject=Feedback%20-%20Career%20Companion"
              className="font-semibold text-blue-600 underline-offset-4 transition duration-200 ease-out hover:underline dark:text-blue-400"
            >
              Feedback / Help
            </a>
            <p className="text-xs leading-4 text-zinc-400 dark:text-zinc-500">Built for IBM SkillsBuild AICTE Internship</p>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
