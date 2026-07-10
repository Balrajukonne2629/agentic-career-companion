
# Agentic Career Counseling Companion

**AI-powered career onboarding and guidance platform for engineering students.**

Collects a student's profile (via voice or manual input), validates and scores it, ranks the best-fit career paths, identifies missing skills, and generates a personalized 30/60/90-day learning roadmap — through a 5-agent pipeline powered by IBM watsonx.ai (Granite).

🔗 **Live Demo:** [agentic-career-companion.vercel.app](https://agentic-career-companion.vercel.app/)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Testing](#testing)
- [Deployment](#deployment)
- [Acknowledgments](#acknowledgments)

---

## Overview

Most career-guidance tools give generic, one-size-fits-all advice. This project takes a student's actual academic profile and interests, and produces career recommendations, skill-gap analysis, and a learning roadmap grounded in that specific profile — not a static template.

The system is built as a **hybrid pipeline**: deterministic logic (validation, scoring, gap analysis) runs in Python for speed and reliability, while IBM Granite is reserved for the parts that genuinely need language reasoning — career recommendation narratives and roadmap generation.

## Architecture

```
Student Input (Text / Voice)
        │
        ▼
┌─────────────────┐
│ Validation Agent │  Extracts & normalizes CGPA, year, skills, interests
└────────┬─────────┘
         ▼
┌─────────────────┐
│  Profile Agent   │  Computes readiness score, profile tier, time-to-ready
└────────┬─────────┘
         ▼
┌─────────────────┐
│  Career Agent    │  Ranks top 3 career matches (IBM Granite)
└────────┬─────────┘
         ▼
┌─────────────────┐
│ Skill Gap Agent  │  Set-difference against target career skill profile
└────────┬─────────┘
         ▼
┌─────────────────┐
│ Roadmap Agent    │  Generates 30/60/90-day plan (IBM Granite)
└────────┬─────────┘
         ▼
  Interactive Dashboard
```

**Design principle:** Python agents never block on an LLM call — Granite is only invoked for the two agents where open-ended generation actually adds value (Career, Roadmap), keeping the pipeline fast, cheap, and resilient.

### Key Features

| Feature | Description |
|---|---|
| **Multi-Agent Pipeline** | 5 specialized agents, each with one responsibility, passing structured JSON downstream |
| **Fault-Tolerant Fallback** | Gracefully degrades to local heuristics if the watsonx.ai API is rate-limited (HTTP 429), times out, or is offline |
| **Voice & Text Input** | Browser Web Speech API, with optional IBM Speech-to-Text integration |
| **Deterministic Scoring** | CGPA, skills, and interest-based scoring computed in pure Python — auditable and fast |
| **Exportable Career Report** | Dashboard output can be exported for the student's own records |

## Tech Stack

**Frontend** — React, Vite, TailwindCSS, Framer Motion, Axios
**Backend** — Flask, Flask-CORS, Flask-Session, python-dotenv, Gunicorn
**AI Engine** — IBM watsonx.ai SDK, Granite model (`granite-4.0-h-small`)

## Project Structure

```text
├── backend/
│   ├── agents/            # Pipeline agents (validation, profile, career, skill-gap, roadmap)
│   ├── data/               # Career knowledge base (career_data.json)
│   ├── routes/             # Flask blueprint API routes (health, pipeline, stt)
│   ├── tests/               # 333+ pytest unit and reliability tests
│   ├── utils/               # Watson STT, Granite client, parser utilities
│   ├── app.py               # App factory entry point
│   ├── config.py            # Environment configuration loader
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI widgets
│   │   ├── services/        # API client and backend service modules
│   │   └── App.jsx           # Dashboard container
│   ├── package.json
│   └── copy_build.js         # Postbuild script for static asset copying
└── .gitignore
```

## Getting Started

### Prerequisites
- Python 3.11.9
- Node.js 18+
- An IBM watsonx.ai project with API key

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
.\.venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your credentials:

```env
IBM_API_KEY=your_ibm_cloud_api_key
IBM_PROJECT_ID=your_ibm_watsonx_project_id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=your_secure_session_key
FRONTEND_URL=http://localhost:3000
SESSION_COOKIE_SAMESITE=Lax
FLASK_ENV=development
```

```bash
python app.py
```
Backend runs at `http://localhost:5000`.

### 2. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:3000`.

## Testing

333+ unit and integration tests covering agent logic, fallback behavior, and API routes:

```bash
cd backend
python -m pytest -v
```

## Deployment

### Frontend (Vercel / Netlify)
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Env variable:** `VITE_API_BASE_URL` → your deployed backend URL (e.g. `https://your-backend.onrender.com/api`)

### Backend (Render)
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- **Env variables:** IBM watsonx.ai credentials, `FRONTEND_URL` → your frontend URL, `SESSION_COOKIE_SAMESITE=None` for cross-origin cookie sharing in production
- **Note:** Set `PYTHON_VERSION=3.11.9` (or commit `backend/runtime.txt`) — avoids compiler errors when installing packages like `pandas` on newer Python versions

## Acknowledgments

Built as part of the **IBM SkillsBuild Internship Program**, in collaboration with **Edunet Foundation**, powered by **IBM watsonx.ai** and **Granite Foundation Models**.

---

**Author:** Balraju Konne — B.Tech Information Technology, Chaitanya Bharathi Institute of Technology

