import { Sparkles } from 'lucide-react';
import { projectName, topBarBadge } from '../data/workspaceCopy';
import { aboutData } from '../data/faqData';
import { GitHubIcon, LinkedInIcon } from './SocialIcons';

/**
 * Responsive Footer component
 * @param {{ onNavigate?: (path: string) => void }} props
 */
function Footer({ onNavigate }) {
  const handleNavClick = (event, path) => {
    event.preventDefault();
    if (onNavigate) {
      onNavigate(path);
    }
  };

  return (
    <footer className="relative z-10 border-t border-zinc-200/80 bg-white/40 py-6 sm:py-8 text-sm text-zinc-500 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 md:items-start sm:gap-8">
          {/* Col 1: Brand & Desc */}
          <div className="space-y-2 sm:col-span-2">
            <p className="text-base font-bold text-zinc-800 dark:text-zinc-100">{projectName}</p>
            <p className="max-w-md text-xs leading-5 text-zinc-600 dark:text-zinc-400">
              A multi-agent AI career counseling tool built on IBM watsonx.ai. It analyzes skills, finds career matches, identifies skill gaps, and generates personalized learning roadmaps.
            </p>
            <div className="pt-1.5">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-ibm-blue dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
                <Sparkles className="h-3 w-3" aria-hidden="true" />
                <span>{topBarBadge}</span>
              </span>
            </div>
          </div>

          {/* Col 2: Navigation Links */}
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100">Navigation</p>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="/"
                  onClick={(e) => handleNavClick(e, '/')}
                  className="transition duration-150 hover:text-ibm-blue hover:underline dark:hover:text-blue-400"
                >
                  Home / Workspace
                </a>
              </li>
              <li>
                <a
                  href="/how-it-works"
                  onClick={(e) => handleNavClick(e, '/how-it-works')}
                  className="transition duration-150 hover:text-ibm-blue hover:underline dark:hover:text-blue-400"
                >
                  How It Works
                </a>
              </li>
              <li>
                <a
                  href="/faq"
                  onClick={(e) => handleNavClick(e, '/faq')}
                  className="transition duration-150 hover:text-ibm-blue hover:underline dark:hover:text-blue-400"
                >
                  Frequently Asked Questions
                </a>
              </li>
              <li>
                <a
                  href="/about"
                  onClick={(e) => handleNavClick(e, '/about')}
                  className="transition duration-150 hover:text-ibm-blue hover:underline dark:hover:text-blue-400"
                >
                  About the Project
                </a>
              </li>
            </ul>
          </div>

          {/* Col 3: Connect & Author */}
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-wider text-zinc-900 dark:text-zinc-100">Developer</p>
            <p className="text-xs text-zinc-700 dark:text-zinc-300 font-semibold">{aboutData.author}</p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">{aboutData.college}</p>
            <div className="flex items-center gap-3 pt-1.5">
              <a
                href={aboutData.linkedinUrl}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Balraju Konne on LinkedIn"
                className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 transition duration-150 hover:bg-blue-50 hover:text-ibm-blue dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-blue-950/40 dark:hover:text-blue-400"
              >
                <LinkedInIcon className="h-4 w-4" />
              </a>
              <a
                href={aboutData.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Project on GitHub"
                className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 transition duration-150 hover:bg-zinc-200 hover:text-zinc-950 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700 dark:hover:text-white"
              >
                <GitHubIcon className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-6 sm:mt-8 flex flex-col items-center justify-between gap-2.5 border-t border-zinc-200/60 pt-4 text-xs text-zinc-400 sm:flex-row dark:border-zinc-800/60 dark:text-zinc-500">
          <p>&copy; 2026 {aboutData.author}. All rights reserved.</p>
          <p>Built for the {aboutData.program}</p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
