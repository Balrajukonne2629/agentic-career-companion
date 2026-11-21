import { HelpCircle, ChevronDown, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { faqData } from '../data/faqData';

/**
 * @param {{ onNavigate?: (path: string) => void }} props
 */
function FAQPage({ onNavigate }) {
  const [openItems, setOpenItems] = useState(() => ({
    'what-is-it': true,
    'how-skill-gaps-found': true,
    'which-ai-model': true,
    'is-it-free': true,
    'who-built-it': true,
  }));

  const toggleItem = (id) => {
    setOpenItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <article className="mx-auto w-full max-w-4xl space-y-8 py-4 sm:py-6">
      {/* Header section */}
      <header className="space-y-3 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-200/80 bg-blue-50/80 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-blue-400/20 dark:bg-blue-400/10 dark:text-blue-300">
          <HelpCircle className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Frequently Asked Questions</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-950 sm:text-3xl dark:text-zinc-50">
          Questions &amp; Answers
        </h1>
        <p className="max-w-2xl text-sm leading-6 text-zinc-600 dark:text-zinc-400">
          Everything you need to know about the Agentic Career Companion, multi-agent AI architecture, skill gap identification, and IBM watsonx.ai foundation models.
        </p>
      </header>

      {/* FAQ items list */}
      <div className="space-y-4" role="region" aria-label="Frequently Asked Questions">
        {faqData.map((faq, index) => {
          const isOpen = Boolean(openItems[faq.id]);
          return (
            <section
              key={faq.id}
              className="overflow-hidden rounded-3xl border border-zinc-200/80 bg-white/80 p-5 shadow-sm backdrop-blur-xl transition duration-200 dark:border-white/10 dark:bg-zinc-900/80 sm:p-6"
            >
              <button
                type="button"
                onClick={() => toggleItem(faq.id)}
                aria-expanded={isOpen}
                aria-controls={`faq-answer-${faq.id}`}
                className="flex w-full items-start justify-between gap-4 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-xs font-bold text-ibm-blue dark:bg-blue-950/60 dark:text-blue-400">
                    Q{index + 1}
                  </span>
                  <h2 className="text-base font-semibold leading-7 text-zinc-900 dark:text-zinc-100 sm:text-lg">
                    {faq.question}
                  </h2>
                </div>
                <span
                  className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-zinc-400 transition-transform duration-200 dark:text-zinc-500 ${
                    isOpen ? 'rotate-180 text-ibm-blue dark:text-blue-400' : ''
                  }`}
                  aria-hidden="true"
                >
                  <ChevronDown className="h-4 w-4" />
                </span>
              </button>

              <div
                id={`faq-answer-${faq.id}`}
                role="region"
                aria-labelledby={`faq-question-${faq.id}`}
                className={`mt-3 pl-10 text-sm leading-6 text-zinc-600 transition-all duration-200 dark:text-zinc-300 ${
                  isOpen ? 'block' : 'hidden'
                }`}
              >
                <p>{faq.answer}</p>
              </div>
            </section>
          );
        })}
      </div>

      {/* Call to action */}
      <aside className="rounded-3xl border border-blue-200/80 bg-blue-50/50 p-6 text-center dark:border-blue-400/20 dark:bg-blue-950/20 sm:p-8">
        <Sparkles className="mx-auto h-6 w-6 text-ibm-blue dark:text-blue-400" aria-hidden="true" />
        <h3 className="mt-2 text-lg font-semibold text-zinc-950 dark:text-zinc-50">
          Ready to build your personalized career roadmap?
        </h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-zinc-600 dark:text-zinc-400">
          Speak or type your current skills and target goals to generate a customized 30/60/90-day learning curriculum.
        </p>
        <button
          type="button"
          onClick={() => onNavigate && onNavigate('/')}
          className="mt-4 inline-flex items-center justify-center rounded-full bg-ibm-blue px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition duration-200 hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ibm-blue"
        >
          Start AI Career Assessment
        </button>
      </aside>
    </article>
  );
}

export default FAQPage;
