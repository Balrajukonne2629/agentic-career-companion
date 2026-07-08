# Agentic Career Counseling Companion — Implementation Plan

## Top-Level Overview

Build an AI-powered Agentic Career Counseling Companion using IBM Granite models and
IBM watsonx.ai. Students provide a voice or text introduction; the system extracts their
profile, identifies skill gaps, recommends career paths, and generates a personalized
30/60/90-day learning roadmap — all rendered on a single-page React dashboard.

**Stack:**
- Frontend: React + Tailwind CSS (Web Speech API for STT, Watson STT as fallback)
- Backend: Python Flask (sequential multi-agent pipeline)
- AI: IBM Granite via ibm-watsonx-ai SDK
  - granite-3-8b-instruct → Validation Agent, Profile Agent
  - granite-13b-instruct-v2 → Career Recommendation Agent, Skill Gap Agent, Roadmap Agent
- Knowledge Base: career_data.json (local, versioned schema)
- Session State: Flask server-side session (cookie-backed)
- Deployment: IBM Cloud Foundry (Lite tier)

**Confirmed Decisions:**
- STT: Web Speech API (primary) + IBM Watson STT (fallback)
- Dashboard: Single-page, 4 collapsible sections
- Deployment: IBM Cloud Foundry

---

## Sub-Tasks

---

### Sub-Task 1 — Define the career_data.json Knowledge Base Schema

**Status:** [x] complete

**Intent:**
This is the foundational contract for the entire project. Every agent reads from this
file. If the schema is wrong or incomplete, all five agents break. It must be defined
and finalized before any agent or frontend code is written.

**Expected Outcomes:**
- `backend/data/career_data.json` exists with at least 6 career entries
- Each entry contains: career name, description, required skills, nice-to-have skills,
  certifications, suggested projects, and related roles
- Schema is documented inline so agents can reference field names reliably
- The file is human-editable so career entries can be added without touching agent code

**Todo List:**
1. Create the directory structure: `backend/data/`
2. Define the JSON schema with the following top-level structure:
   ```
   {
     "version": "1.0",
     "careers": [ ...career objects... ]
   }
   ```
3. Each career object must include:
   - `id` (string slug, e.g. "full-stack-developer")
   - `title` (display name)
   - `description` (2–3 sentence overview)
   - `required_skills` (array of strings — must-have for skill gap analysis)
   - `nice_to_have_skills` (array of strings — bonus skills)
   - `certifications` (array of objects: `{ "name", "provider", "url" }`)
   - `suggested_projects` (array of strings)
   - `related_roles` (array of strings)
   - `suitable_for_interests` (array of interest keywords for matching)
4. Populate entries for all 6 target careers:
   - Full Stack Developer
   - Backend Developer
   - Data Analyst
   - Cloud Engineer
   - Cybersecurity Analyst
   - AI/ML Engineer
5. Validate JSON is well-formed and all required fields are present in every entry

**Relevant Context:**
- File path: `backend/data/career_data.json`
- Agents that consume this file: Career Recommendation Agent, Skill Gap Agent,
  Roadmap Agent
- Certifications and suggested_projects fields directly satisfy two problem statement
  requirements that were marked as partial gaps in the architecture review

---

### Sub-Task 2 — Flask Backend Scaffold and watsonx.ai SDK Integration

**Status:** [x] complete

**Intent:**
Set up the Python Flask backend with all dependencies installed, IBM watsonx.ai SDK
configured, and a verified connection to the Granite models. This must be done before
any agent logic is written so that model calls can be tested in isolation.

**Expected Outcomes:**
- Flask app runs locally with no errors
- `ibm-watsonx-ai` SDK is installed and a test prompt returns a valid response from
  both `granite-3-8b-instruct` and `granite-13b-instruct-v2`
- IBM credentials are loaded from a `.env` file (never hardcoded)
- CORS is configured so the React frontend can call Flask APIs
- Flask session is configured for server-side state storage
- `requirements.txt` and `manifest.yml` (for Cloud Foundry) are present

**Todo List:**
1. Create directory structure:
   ```
   backend/
     agents/
     data/
     utils/
     app.py
     config.py
     requirements.txt
     manifest.yml
     .env.example
   ```
2. Install dependencies:
   - flask
   - flask-cors
   - flask-session
   - ibm-watsonx-ai
   - python-dotenv
   - ibm-watson (for Watson STT fallback)
3. Create `config.py` to load IBM_API_KEY, IBM_PROJECT_ID, IBM_WATSONX_URL from `.env`
4. Create `utils/granite_client.py` with two pre-configured client instances:
   - `call_granite_fast(prompt)` → uses granite-3-8b-instruct
   - `call_granite_strong(prompt)` → uses granite-13b-instruct-v2
5. Write a `/api/health` endpoint that calls both models with a test prompt and returns
   their responses — confirms SDK wiring before agent work begins
6. Configure CORS in `app.py` to allow requests from `http://localhost:3000`
7. Create `manifest.yml` for Cloud Foundry deployment with correct memory and
   start command settings
8. Create `.env.example` with placeholder keys documented

**Relevant Context:**
- IBM watsonx.ai SDK: `ibm-watsonx-ai` pip package
- Authentication: IAM API key + Project ID + watsonx.ai regional URL
- Model IDs to use:
  - `ibm/granite-3-8b-instruct` (Validation, Profile agents)
  - `ibm/granite-13b-instruct-v2` (Career, Skill Gap, Roadmap agents)
- Cloud Foundry deployment requires `manifest.yml` and a `Procfile` or start command

---

### Sub-Task 3 — Validation Agent (Speech/Text Extraction + Gap Detection)

**Status:** [x] complete

**Intent:**
This is the entry point of the entire pipeline. It receives raw speech transcript or
typed text, extracts structured profile fields, identifies missing required fields,
and either returns a complete profile JSON or a list of follow-up questions for only
the missing fields. Uses granite-3-8b-instruct for speed.

**Expected Outcomes:**
- `POST /api/validate` accepts `{ "transcript": "...", "partial_profile": {...} }`
- Agent runs a two-pass Granite prompt strategy:
  - Pass 1: Extract all detectable fields into a JSON profile
  - Pass 2: Compare extracted profile against required schema, return missing fields
- If all fields are present: returns `{ "status": "complete", "profile": {...} }`
- If fields are missing: returns `{ "status": "incomplete", "missing_fields": [...],
  "partial_profile": {...} }`
- Frontend uses `missing_fields` list to ask only targeted follow-up questions
- Extracted profile is stored in Flask session

**Required Profile Fields:**
- name, branch, year, cgpa, skills (array), interests (array), career_goal

**Todo List:**
1. Create `backend/agents/validation_agent.py`
2. Write Pass 1 prompt: instruct Granite to extract name, branch, year, cgpa, skills,
   interests, career_goal from free-form text and return strict JSON only
3. Add JSON parsing with error handling — if Granite returns malformed JSON, retry once
   with a stricter prompt before raising an error
4. Write Pass 2 logic: compare extracted JSON keys against required field list in Python
   (do NOT use Granite for this — it is simple set comparison logic)
5. Write the `/api/validate` Flask route in `app.py`
6. Store the partial or complete profile in `session["student_profile"]`
7. Return structured response with status, profile, and missing_fields list
8. Write unit tests for the agent with at least 3 transcript examples:
   - Complete introduction (all fields present)
   - Partial introduction (missing CGPA and interests)
   - Minimal introduction (only name present)

**Relevant Context:**
- Model: `granite-3-8b-instruct` via `call_granite_fast()`
- The two-pass strategy prevents hallucination — Pass 2 gap detection is pure Python
- `partial_profile` in the request body allows the frontend to merge follow-up answers
  back into the existing partial profile across multiple calls
- This agent is the hardest to prompt-engineer correctly; test it in watsonx.ai
  Prompt Lab before coding

---

### Sub-Task 4 — Profile Agent (Strengths Analysis and Summary)

**Status:** [x] complete

**Intent:**
Takes the validated student profile JSON and generates a human-readable profile
summary with identified strengths. This output is displayed in the first collapsible
section of the dashboard and also feeds context into the Career Recommendation Agent.
Uses granite-3-8b-instruct.

**Expected Outcomes:**
- `POST /api/profile` accepts the validated profile JSON (or reads from session)
- Returns a profile analysis containing:
  - `summary` (2–3 sentence student overview)
  - `strengths` (array of identified strength statements)
  - `profile_tier` (e.g. "strong", "moderate", "needs-development" based on CGPA
    and skills count — determined by Python logic, not LLM)
- Result is stored in `session["profile_analysis"]`

**Todo List:**
1. Create `backend/agents/profile_agent.py`
2. Write Python logic to compute `profile_tier` from CGPA thresholds and skills count
   (no LLM needed for this — it is deterministic rule logic)
3. Write Granite prompt to generate a personalized `summary` and `strengths` array
   from the profile JSON — instruct model to return strict JSON only
4. Add JSON parsing with retry on malformed response
5. Write the `/api/profile` Flask route
6. Store result in session and return to frontend

**Relevant Context:**
- Model: `granite-3-8b-instruct` via `call_granite_fast()`
- `profile_tier` is computed in Python: CGPA >= 8.0 + skills >= 4 = "strong",
  CGPA >= 6.5 + skills >= 2 = "moderate", else "needs-development"
- The summary and strengths from this agent are passed as context to the Career
  Recommendation Agent prompt to improve recommendation relevance

---

### Sub-Task 5 — Career Recommendation Agent

**Status:** [x] complete

**Intent:**
Compares the student profile against all careers in `career_data.json` and recommends
the top 3 most suitable career paths with reasoning. Uses granite-13b-instruct-v2 for
stronger reasoning quality. The knowledge base is injected directly into the prompt as
context (RAG-style, no vector database needed).

**Expected Outcomes:**
- `POST /api/recommend` reads profile and profile analysis from session
- Loads `career_data.json` and injects career summaries into the Granite prompt
- Returns top 3 recommended careers ranked by fit, each with:
  - `career_id` (matches career_data.json id field)
  - `title`
  - `match_score` (1–10 integer, computed by agent reasoning)
  - `reasoning` (2–3 sentence explanation)
  - `matching_skills` (student skills that already align)
- Result is stored in `session["recommendations"]`

**Todo List:**
1. Create `backend/agents/career_recommendation_agent.py`
2. Write a function to load and serialize `career_data.json` careers into a
   compact prompt-friendly text block (title + required_skills + suitable_for_interests)
3. Write Granite prompt that:
   - Receives student profile + profile summary as context
   - Receives the careers text block
   - Is instructed to return exactly 3 recommendations as a strict JSON array
4. Add JSON parsing with retry logic
5. Write the `/api/recommend` Flask route
6. Store result in session and return to frontend
7. Add a fallback: if Granite returns fewer than 3 valid careers, fill remaining slots
   using a Python-based keyword matching function against `career_data.json`

**Relevant Context:**
- Model: `granite-13b-instruct-v2` via `call_granite_strong()`
- Keep the injected career data block under ~1500 tokens — use only title,
  required_skills, and suitable_for_interests fields in the prompt (not full career
  objects) to stay within context limits
- The fallback keyword matcher ensures robustness even if the LLM call fails

---

### Sub-Task 6 — Skill Gap Agent

**Status:** [x] complete

**Intent:**
Takes the student's current skills and the top recommended career from the Career
Recommendation Agent, looks up the target career's required_skills from career_data.json,
and produces a prioritized skill gap report. Uses granite-13b-instruct-v2 to generate
learning priority reasoning.

**Expected Outcomes:**
- `POST /api/skillgap` reads profile and top recommendation from session
- Performs a Python set-difference between student skills and career required_skills
  to identify gaps (deterministic — no LLM needed for the gap computation itself)
- Uses Granite to generate a prioritized learning order and brief explanation for
  each missing skill
- Returns:
  - `target_career` (title)
  - `current_skills` (student's existing skills)
  - `skills_to_learn` (array of objects: `{ "skill", "priority", "reason" }`)
  - `skills_already_have` (matching skills student already possesses)
- Result is stored in `session["skill_gap"]`

**Todo List:**
1. Create `backend/agents/skill_gap_agent.py`
2. Write Python set-difference logic: `gaps = required_skills - student_skills`
   (case-insensitive comparison)
3. Write Granite prompt to prioritize the gap list and explain why each skill matters
   for the target career — return strict JSON array
4. Add JSON parsing with retry logic
5. Write the `/api/skillgap` Flask route
6. Store result in session and return to frontend

**Relevant Context:**
- Model: `granite-13b-instruct-v2` via `call_granite_strong()`
- The set-difference is done in Python — Granite is only used for prioritization
  reasoning, not for identifying gaps (prevents hallucination of non-existent skills)
- Use the first item in `session["recommendations"]` as the target career
- Priority levels: "critical" (core language/framework), "important" (tooling),
  "beneficial" (nice-to-have)

---

### Sub-Task 7 — Roadmap Generation Agent

**Status:** [x] complete

**Intent:**
Generates a personalized 30/60/90-day learning roadmap based on the skill gap report
and the target career's certifications and suggested_projects from career_data.json.
This is the most content-rich agent output and uses granite-13b-instruct-v2.

**Expected Outcomes:**
- `POST /api/roadmap` reads skill gap and recommendations from session
- Returns a structured roadmap:
  ```
  {
    "target_career": "...",
    "30_day": { "focus": "...", "goals": [...], "resources": [...] },
    "60_day": { "focus": "...", "goals": [...], "resources": [...] },
    "90_day": { "focus": "...", "goals": [...], "certifications": [...],
                "projects": [...] }
  }
  ```
- Certifications in 90-day plan are pulled directly from `career_data.json`
  (not hallucinated by the model)
- Suggested projects in 90-day plan are pulled directly from `career_data.json`
- Result is stored in `session["roadmap"]`

**Todo List:**
1. Create `backend/agents/roadmap_agent.py`
2. Load certifications and suggested_projects from `career_data.json` for the
   target career — inject these as hard facts into the Granite prompt
3. Write Granite prompt to generate 30/60/90 day focus areas, goals, and resources
   — instruct model to incorporate the provided certifications and projects
4. Add JSON parsing with retry logic
5. Write the `/api/roadmap` Flask route
6. Store result in session and return to frontend

**Relevant Context:**
- Model: `granite-13b-instruct-v2` via `call_granite_strong()`
- Certifications and projects are injected from `career_data.json` — the model is
  instructed to incorporate them, not invent new ones. This prevents hallucinated
  certification names.
- 30-day focus: foundational missing skills
- 60-day focus: intermediate skills + first project
- 90-day focus: advanced skills + certifications + portfolio project

---

### Sub-Task 8 — Speech-to-Text Integration (Web Speech API + Watson STT Fallback)

**Status:** [x] complete

**Intent:**
Implement the voice input feature that is the core UX differentiator of this project.
The browser uses the Web Speech API by default. If the browser does not support it
(e.g. Firefox without flag, or user denies microphone), the frontend falls back to
recording audio and sending it to a Flask endpoint that calls IBM Watson STT.

**Expected Outcomes:**
- React component `VoiceInput.jsx` renders a microphone button
- On click: attempts Web Speech API recognition
- If Web Speech API is unavailable or fails: switches to Watson STT fallback
- A visible indicator shows which STT mode is active ("Browser" or "IBM Watson")
- Transcript text is populated into the text input field after recognition
- User can edit the transcript before submitting

**Todo List:**
1. Create `frontend/src/components/VoiceInput.jsx`
2. Implement Web Speech API recognition using `window.SpeechRecognition` or
   `window.webkitSpeechRecognition`
3. Detect browser support on component mount; set state flag `useWatsonFallback`
   if Web Speech API is unavailable
4. For Watson STT fallback:
   a. Record audio using MediaRecorder API in the browser
   b. Send audio blob to `POST /api/stt` Flask endpoint
   c. Flask endpoint calls IBM Watson Speech to Text SDK
   d. Return transcript text to frontend
5. Create `backend/utils/watson_stt.py` with Watson STT client initialization
   and a `transcribe_audio(audio_bytes)` function
6. Write `POST /api/stt` route in `app.py`
7. Display STT mode indicator badge in the UI

**Relevant Context:**
- IBM Watson STT credentials are separate from watsonx.ai credentials — need a
  separate Watson STT service instance created on IBM Cloud Lite
- Watson STT free tier: 500 minutes/month — sufficient for demo use
- Web Speech API is supported in Chrome and Edge natively; Firefox requires a flag
- The user can always type their introduction manually as a third fallback

---

### Sub-Task 9 — React Frontend: Voice Input Page and Agent Pipeline Trigger

**Status:** [ ] pending

**Intent:**
Build the main input page of the React application. This page handles voice/text input,
displays follow-up questions for missing profile fields, and triggers the full agent
pipeline once the profile is complete.

**Expected Outcomes:**
- Landing page with app title, brief description, and microphone button
- VoiceInput component integrated for speech capture
- Transcript displayed in an editable text area after capture
- On submit: calls `/api/validate` and handles both complete and incomplete responses
- If incomplete: renders targeted follow-up input fields for only the missing fields
- On profile completion: triggers `/api/profile` → `/api/recommend` → `/api/skillgap`
  → `/api/roadmap` in sequence, showing a progress indicator for each step
- On pipeline completion: navigates to the Career Dashboard

**Todo List:**
1. Scaffold React app with Tailwind CSS in `frontend/`
2. Create `frontend/src/pages/InputPage.jsx` as the main landing page
3. Integrate `VoiceInput.jsx` component
4. Implement the submit → validate → follow-up loop using React state
5. Build a `MissingFieldsForm.jsx` component that dynamically renders inputs for
   only the fields listed in the `missing_fields` API response
6. Implement sequential agent pipeline calls with a `PipelineProgress.jsx` component
   showing current step (Analyzing Profile → Finding Careers → Checking Skill Gaps
   → Building Roadmap)
7. Store complete pipeline results in React context or local state for the dashboard
8. Navigate to `/dashboard` on pipeline completion

**Relevant Context:**
- Use `axios` or `fetch` for API calls to Flask backend
- Pipeline must be sequential (each call depends on session state set by prior call)
- Progress indicator improves perceived performance during Granite API latency
- All agent calls use session state on the backend — no need to pass full data
  between frontend calls, just trigger each endpoint in order

---

### Sub-Task 10 — React Frontend: Career Dashboard (4 Collapsible Sections)

**Status:** [ ] pending

**Intent:**
Build the single-page Career Dashboard that renders all agent outputs in four
collapsible sections. This is the primary deliverable the student sees and the
main demo surface for the IBM evaluation.

**Expected Outcomes:**
- `/dashboard` route renders the Career Dashboard page
- Four collapsible sections, all open by default:
  1. **Profile Summary** — student info card + strengths list + profile tier badge
  2. **Career Recommendations** — top 3 career cards with match score, reasoning,
     and matching skills
  3. **Skill Gap Report** — current skills vs. skills to learn, with priority badges
     (Critical / Important / Beneficial)
  4. **30/60/90 Day Roadmap** — tabbed or accordion view per time period, showing
     focus area, goals, resources, certifications, and projects
- Each section has a collapse/expand toggle
- "Start Over" button clears session and returns to Input Page
- Page is fully responsive (mobile-friendly via Tailwind)

**Todo List:**
1. Create `frontend/src/pages/DashboardPage.jsx`
2. Create reusable `CollapsibleSection.jsx` wrapper component
3. Build `ProfileCard.jsx` — displays name, branch, year, CGPA, skills chips,
   profile tier badge, and AI-generated strengths
4. Build `CareerRecommendationCards.jsx` — 3 cards with career title, match score
   progress bar, reasoning text, and matching skill chips
5. Build `SkillGapReport.jsx` — two columns: "Skills You Have" (green) vs
   "Skills to Learn" (with priority badge coloring)
6. Build `RoadmapView.jsx` — three tab panels (30/60/90 days), each showing
   focus headline, goals list, resources list, and (for 90-day) certifications
   and projects
7. Wire all components to the pipeline result data from React context/state
8. Add "Start Over" button that calls `DELETE /api/session` and redirects to `/`
9. Apply consistent Tailwind styling with IBM-inspired color palette
   (IBM Blue: #0062ff, dark backgrounds, clean typography)

**Relevant Context:**
- All data is already in React state from the pipeline calls in Sub-Task 9
- Match score (1–10) should be rendered as a visual progress bar or ring
- Priority badges: Critical = red, Important = amber, Beneficial = green
- The dashboard is the primary demo screen — prioritize visual clarity over
  feature density

---

### Sub-Task 11 — IBM Cloud Foundry Deployment

**Status:** [ ] pending

**Intent:**
Deploy the complete application to IBM Cloud Foundry (Lite tier) so it is accessible
via a public URL for the IBM SkillsBuild demo and evaluation. The Flask backend serves
both the API routes and the built React static files.

**Expected Outcomes:**
- React app is built (`npm run build`) and output is placed in `backend/static/`
- Flask serves the React build from the `/` route
- Application is deployed to IBM Cloud Foundry and accessible at a public URL
- All environment variables (IBM_API_KEY, IBM_PROJECT_ID, etc.) are set as Cloud
  Foundry environment variables (not in the deployed code)
- `manifest.yml` correctly specifies app name, memory (512MB), and start command

**Todo List:**
1. Update Flask `app.py` to serve React's `index.html` from `static/` for all
   non-API routes (catch-all route for React Router support)
2. Add a `build.sh` script that runs `npm run build` in `frontend/` and copies
   the output to `backend/static/`
3. Finalize `manifest.yml`:
   - memory: 512M
   - buildpack: python_buildpack
   - start command: `gunicorn app:app`
4. Add `gunicorn` to `requirements.txt`
5. Run `build.sh` to produce the final static build
6. Use IBM Cloud CLI (`ibmcloud cf push`) to deploy
7. Set environment variables via `ibmcloud cf set-env` for all secrets
8. Verify the public URL loads the app and all API routes respond correctly
9. Test voice input and full pipeline end-to-end on the deployed URL

**Relevant Context:**
- IBM Cloud Foundry Lite: 256MB default, request 512MB in manifest for safety
- `python_buildpack` handles `requirements.txt` automatically
- Flask must NOT run in debug mode in production (`debug=False`)
- Watson STT fallback requires the Watson STT service to be bound to the
  Cloud Foundry app or credentials set as environment variables

---

## Implementation Order and Dependencies

```
Sub-Task 1  (career_data.json)
     ↓
Sub-Task 2  (Flask scaffold + SDK)
     ↓
Sub-Tasks 3–7  (Agents, in order: Validation → Profile → Career → SkillGap → Roadmap)
     ↓
Sub-Task 8  (STT integration)
     ↓
Sub-Tasks 9–10  (React frontend: Input Page → Dashboard)
     ↓
Sub-Task 11  (Cloud Foundry deployment)
```

Sub-Tasks 3–7 must be done sequentially (each agent feeds the next).
Sub-Tasks 8, 9, 10 can be done in parallel with agents once Sub-Task 2 is complete.

---

## Key Architectural Decisions (Confirmed)

| Decision | Choice | Rationale |
|---|---|---|
| STT Primary | Web Speech API | Free, no quota, works in Chrome/Edge |
| STT Fallback | IBM Watson STT | Stays on IBM stack, 500 min/month free |
| Validation Model | granite-3-8b-instruct | Speed priority for extraction tasks |
| Reasoning Models | granite-13b-instruct-v2 | Quality priority for career/roadmap |
| Knowledge Base | Local JSON file | No DB, no training, Lite-tier safe |
| State Management | Flask session | No DB needed, handles multi-step flow |
| Deployment | IBM Cloud Foundry | Lite tier, traditional PaaS, stable |
| Dashboard | Single-page 4 sections | Focused scope, clear demo surface |

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Granite returns malformed JSON | Two-pass prompting + retry logic in every agent |
| Web Speech API unavailable | Watson STT fallback implemented in Sub-Task 8 |
| career_data.json schema mismatch | Schema defined first in Sub-Task 1 before all agents |
| Granite context limit exceeded | Career data injected as compact summaries not full objects |
| Cloud Foundry memory limit | 512MB manifest + gunicorn with single worker |
| Session loss on CF restart | Acceptable for demo; document as known limitation |
