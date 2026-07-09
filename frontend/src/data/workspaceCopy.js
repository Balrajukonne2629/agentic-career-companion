export const modeOptions = [
  { key: 'speak', label: 'Speak', subtitle: 'Talk naturally', icon: 'Mic' },
  { key: 'write', label: 'Write', subtitle: 'Type your introduction', icon: 'PenLine' },
];

export const topBarBadge = 'Powered by IBM Granite & watsonx.ai';

export const projectName = 'Agentic Career Counseling Companion';

export const projectSubtitle =
  'An AI workspace that turns your background, goals, and strengths into a personalized career roadmap.';

export const infoSections = [
  {
    title: 'About Project',
    detail: 'A focused career counseling companion for students, built around agentic AI profile understanding and roadmap generation.',
  },
  {
    title: 'How It Works',
    detail: 'Share a natural introduction, review the captured profile, then let the agent pipeline validate, analyze, recommend, and plan.',
  },
  {
    title: 'AI Agents',
    detail: 'Validation, Profile, Career, Skill Gap, and Roadmap agents each handle one clear step in the guidance flow.',
  },
  {
    title: 'Privacy & Security',
    detail: 'Your introduction is used for the roadmap experience. Review always happens before analysis begins.',
  },
];

export const howItWorksStages = [
  {
    key: 'validation',
    title: 'Validation',
    detail: 'Extracts the student profile from the introduction.',
  },
  {
    key: 'profile',
    title: 'Profile Analysis',
    detail: 'Summarizes strengths, readiness, and context.',
  },
  {
    key: 'career',
    title: 'Career Recommendation',
    detail: 'Ranks relevant career paths from the knowledge base.',
  },
  {
    key: 'skillgap',
    title: 'Skill Gap Analysis',
    detail: 'Prioritizes missing skills and tools for the target role.',
  },
  {
    key: 'roadmap',
    title: 'Personalized Roadmap',
    detail: 'Turns the analysis into a practical learning plan.',
  },
];

export const introTags = ['Current Year', 'Skills', 'Interests', 'CGPA', 'Career Goal'];

export const speakExample =
  'Hi, I\'m Asha, a second-year B.Tech Information Technology student. I enjoy building web apps with React and JavaScript, and I want to become a full stack developer. My current CGPA is 8.4, and I can study around 10 hours per week.';

export const speakSampleTranscript = [
  'Hi, I\'m Asha, a second-year B.Tech Information Technology student.',
  'I enjoy building web apps with React and JavaScript.',
  'My CGPA is 8.4 and I want to become a full stack developer.',
].join(' ');

export const writeExample = [
  'Hi, I\'m Alex.',
  'I\'m a second-year Computer Science student.',
  'I enjoy building web applications using React and Java.',
  'My CGPA is 8.5.',
  'I want to become a Full Stack Developer.',
].join('\n');

export const pipelinePreviewStages = [
  { key: 'validation', label: 'Validation', state: 'idle' },
  { key: 'profile', label: 'Profile', state: 'idle' },
  { key: 'career', label: 'Career', state: 'idle' },
  { key: 'skillgap', label: 'Skill Gap', state: 'idle' },
  { key: 'roadmap', label: 'Roadmap', state: 'idle' },
];

export const pipelineMockSnippets = {
  validation: 'Profile successfully analyzed.',
  profile: 'Career readiness profile generated.',
  career: 'Career recommendations generated.',
  skillgap: 'Skill gap analysis complete.',
  roadmap: 'Personalized roadmap generated.',
};

export const loadingMockStages = [
  { label: 'Validation Agent', status: 'done' },
  { label: 'Profile Agent', status: 'active' },
  { label: 'Career Agent', status: 'idle' },
  { label: 'Skill Gap Agent', status: 'idle' },
  { label: 'Roadmap Agent', status: 'idle' },
];

export const pipelineRowConfig = [
  {
    key: 'validation',
    label: 'Validation Agent',
    description: 'Extracts structured profile data from the introduction.',
  },
  {
    key: 'profile',
    label: 'Profile Agent',
    description: 'Builds a profile summary and readiness snapshot.',
  },
  {
    key: 'career',
    label: 'Career Agent',
    description: 'Ranks the most relevant career options.',
  },
  {
    key: 'skillgap',
    label: 'Skill Gap Agent',
    description: 'Highlights missing skills and tools in priority order.',
  },
  {
    key: 'roadmap',
    label: 'Roadmap Agent',
    description: 'Transforms the analysis into a learning plan.',
  },
];

export const dashboardPreviewCards = [
  {
    title: 'Profile Summary',
    detail: 'Validated student context and readiness snapshot.',
  },
  {
    title: 'Career Recommendations',
    detail: 'Top 3 career paths with reasoning and matching skills.',
  },
  {
    title: 'Roadmap',
    detail: 'A clean 30/60/90-day plan for the target path.',
  },
];

export const MIN_SPEAK_CHARS = 110;
export const MIN_WRITE_CHARS = 90;
export const MAX_WRITE_CHARS = 1500;

export const STORAGE_KEYS = {
  mode: 'acc.mode',
  theme: 'acc.theme',
};

export function createInitialPipelineRows() {
  return pipelineRowConfig.map((row) => ({
    ...row,
    state: 'idle',
    snippet: '',
  }));
}

export function getPipelinePreviewFromRows(rows) {
  return rows.map((row) => ({
    key: row.key,
    label: row.label.replace(' Agent', ''),
    state: row.state,
  }));
}
