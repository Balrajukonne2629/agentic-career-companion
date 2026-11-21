import { AnimatePresence, motion } from 'framer-motion';
import { BrainCircuit, HelpCircle, Home, Layers, Menu, Moon, Sun, User, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { projectName } from '../data/workspaceCopy';

/**
 * Responsive navigation bar with mobile hamburger menu
 * @param {{
 *   theme: 'light' | 'dark',
 *   onToggleTheme: () => void,
 *   currentPath?: string,
 *   onNavigate?: (path: string) => void
 * }} props
 */
function TopBar({ theme, onToggleTheme, currentPath = '/', onNavigate }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!mobileMenuOpen || typeof window === 'undefined') return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setMobileMenuOpen(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen]);

  const handleNavClick = (event, path) => {
    event.preventDefault();
    setMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate(path);
    }
  };

  const navLinks = [
    { label: 'Home', path: '/', icon: Home },
    { label: 'How It Works', path: '/how-it-works', icon: Layers },
    { label: 'FAQ', path: '/faq', icon: HelpCircle },
    { label: 'About', path: '/about', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200/60 bg-white/80 backdrop-blur-2xl dark:border-white/5 dark:bg-zinc-950/80">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-3.5 sm:px-6 lg:px-8">
        {/* Brand logo & title */}
        <a
          href="/"
          onClick={(e) => handleNavClick(e, '/')}
          className="flex min-w-0 items-center gap-2 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue"
          aria-label="Agentic Career Companion Home"
        >
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-zinc-950 text-white shadow-sm dark:bg-white dark:text-zinc-950">
            <BrainCircuit className="h-4 w-4" aria-hidden="true" />
          </div>
          <span className="truncate text-sm font-bold tracking-tight text-zinc-950 dark:text-zinc-50">
            <span className="hidden sm:inline">{projectName}</span>
            <span className="sm:hidden">Career Companion</span>
          </span>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="hidden items-center gap-1 md:flex" aria-label="Main navigation">
          {navLinks.map((link) => {
            const isActive = currentPath === link.path;
            return (
              <a
                key={link.path}
                href={link.path}
                onClick={(e) => handleNavClick(e, link.path)}
                className={`rounded-full px-3.5 py-1.5 text-xs font-semibold transition duration-150 ${
                  isActive
                    ? 'bg-zinc-950 text-white shadow-sm dark:bg-white dark:text-zinc-950'
                    : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-800/80 dark:hover:text-zinc-50'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                {link.label}
              </a>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="flex items-center gap-1.5">
          {/* Theme Toggle */}
          <button
            type="button"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-600 transition duration-200 ease-out hover:bg-zinc-950/5 hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue dark:text-zinc-300 dark:hover:bg-white/10 dark:hover:text-zinc-50"
          >
            {theme === 'dark' ? <Moon className="h-4 w-4" aria-hidden="true" /> : <Sun className="h-4 w-4" aria-hidden="true" />}
          </button>

          {/* Mobile Menu Hamburger Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-navigation-menu"
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-zinc-600 transition duration-200 ease-out hover:bg-zinc-950/5 hover:text-zinc-950 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue md:hidden dark:text-zinc-300 dark:hover:bg-white/10 dark:hover:text-zinc-50"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" aria-hidden="true" /> : <Menu className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>
      </div>

      {/* Mobile Collapsible Navigation Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            id="mobile-navigation-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            className="overflow-hidden border-b border-zinc-200/80 bg-white/95 px-4 pb-4 pt-2 shadow-lg backdrop-blur-2xl md:hidden dark:border-white/10 dark:bg-zinc-950/95"
          >
            <nav className="flex flex-col gap-1" aria-label="Mobile navigation">
              {navLinks.map((link) => {
                const IconComponent = link.icon;
                const isActive = currentPath === link.path;
                return (
                  <a
                    key={link.path}
                    href={link.path}
                    onClick={(e) => handleNavClick(e, link.path)}
                    className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${
                      isActive
                        ? 'bg-ibm-blue text-white shadow-sm'
                        : 'text-zinc-700 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-900'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <IconComponent className="h-4 w-4" aria-hidden="true" />
                    <span>{link.label}</span>
                  </a>
                );
              })}
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}

export default TopBar;
