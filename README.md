# Agentic Career Counseling Companion

An AI-powered onboarding and career counseling advisor designed for computer science and engineering students. The application collects student transcripts (via speech-to-text or manual input), validates profile information, computes readiness scores, ranks career paths, identifies skill gaps, and maps out a dynamic 30/60/90-day learning curriculum.

Built with **React (Vite)** on the frontend, a **Flask Python** server on the backend, and powered by **IBM watsonx.ai (Granite-4-h-small)**.

---

## 🚀 Key Features

* **Multi-Agent Architecture:** A modular processing pipeline of 5 dedicated agents:
  1. **Validation Agent:** Extracts credentials, normalizes scores (CGPA, year), and flags missing info.
  2. **Profile Agent:** Calculates profile tiers, readiness scores (0-100), and estimates time-to-ready.
  3. **Career Agent:** Performs deterministic scoring and matches students to the top 3 best-suited careers.
  4. **Skill Gap Agent:** Computes exact set-differences to list missing tools and required/nice-to-have skills.
  5. **Roadmap Agent:** Structures a personalized 30/60/90-day curriculum with target projects and certifications.
* **Fault-Tolerant Fallback Architecture:** Automatically degrades gracefully to pure Python extraction and local heuristics if the IBM watsonx.ai API is rate-limited (HTTP 429), timed out, or offline.
* **Flexible Voice & Speech Input:** Employs browser Web Speech API for voice interactions with optional IBM Speech-To-Text client support.

---

## 🛠️ Tech Stack

* **Frontend:** React, Vite, Framer Motion, TailwindCSS, Axios
* **Backend:** Flask, Flask-CORS, Flask-Session, python-dotenv, Gunicorn
* **AI Engine:** IBM watsonx.ai SDK, Granite Models (fast/strong text generator APIs)

---

## 📂 Project Structure

```text
├── backend/
│   ├── agents/            # Pipeline agents (validation, profile, career, etc.)
│   ├── data/              # Career knowledge base (career_data.json)
│   ├── routes/            # Flask blueprint API routes (health, pipeline, stt)
│   ├── tests/             # 333+ pytest unit and reliability test suites
│   ├── utils/             # Watson STT, Granite client, and parser utilities
│   ├── app.py             # App factory entry point
│   ├── config.py          # Environment configuration loader
│   └── requirements.txt   # Python packages
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI widgets
│   │   ├── services/      # apiClient and backend service modules
│   │   └── App.jsx        # Dashboard container
│   ├── package.json       # Node package manager configuration
│   └── copy_build.js      # Postbuild script copying static build assets
└── .gitignore             # Git exclusion rules
```

---

## 🖥️ Local Installation & Setup

### 1. Backend Setup
Clone the repository, navigate to the `backend` folder, and configure a virtual environment:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # On Windows (PowerShell)
source .venv/bin/activate  # On macOS/Linux

pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the `backend/` directory by copying `.env.example` and filling in the values:
```env
IBM_API_KEY=your_ibm_cloud_api_key
IBM_PROJECT_ID=your_ibm_watsonx_project_id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=your_secure_session_key
FRONTEND_URL=http://localhost:3000
SESSION_COOKIE_SAMESITE=Lax
FLASK_ENV=development
```

Start the Flask server:
```powershell
python app.py
```
The server will boot on `http://localhost:5000`.

### 2. Frontend Setup
Navigate to the `frontend` folder and install dependencies:

```powershell
cd ../frontend
npm install
```

Start the frontend development server:
```powershell
npm run dev
```
The client will run on `http://localhost:3000`.

---

## 🧪 Testing

The backend includes a comprehensive test suite of 333 unit and integration tests. Run the suite inside the active virtual environment:

```powershell
cd backend
python -m pytest -v
```

---

## ☁️ Deployment

### Frontend (Vercel / Netlify)
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Env Variable:** Set `VITE_API_BASE_URL` to your deployed backend domain (e.g., `https://your-backend.onrender.com/api`).

### Backend (Render)
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `gunicorn app:app`
* **Env Variables:** Configure IBM watsonx.ai credentials, `FRONTEND_URL` pointing to your Vercel/Netlify URL, and set `SESSION_COOKIE_SAMESITE=None` to ensure cookie-sharing works.
