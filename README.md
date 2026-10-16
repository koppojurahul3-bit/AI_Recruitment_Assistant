# AI Recruitment Assistant — V2

An AI-assisted recruitment workspace for resume screening, candidate matching, interview preparation, scheduling, and recruitment reporting. V2 adds a React frontend backed by a FastAPI API while retaining the existing Streamlit application.

> **Current development version:** `v2-development`  
> **V1:** preserved on `main`. V2 has not been merged into `main`.

## Overview

Recruiters can analyze PDF resumes against a job description, review candidate matches and rankings, inspect recruitment analytics, prepare interview questions, manage interview schedule records, and export candidate reports. The React interface communicates with a local FastAPI service. Optional AI-assisted features use a locally running Ollama model.

## Features

- PDF resume and job-description analysis
- Candidate skill extraction, ATS-style scoring, matching, and ranking
- Candidate review and recruitment analytics
- Interview question generation and written-answer evaluation
- Interview schedule records
- Recruiter question answering and recruitment task assistance through Ollama
- Candidate report export (CSV)
- React dashboard with FastAPI integration
- Existing Streamlit interface retained for compatibility

Feature availability depends on the selected interface, installed dependencies, and whether Ollama is running.

## Tech stack

- **Frontend:** React, Vite, JavaScript, Tailwind CSS, Recharts, Framer Motion
- **API:** Python, FastAPI, Uvicorn
- **Resume and reporting:** pypdf, pandas, ReportLab
- **AI runtime (optional):** Ollama with a locally installed model
- **Testing:** pytest

## Architecture

```text
Recruiter
   |
   v
React + Vite frontend (port 5173/5174)
   |
   v
FastAPI backend (127.0.0.1:8765)
   |                         |
   v                         v
Resume analysis/services    Ollama (optional, local)
   |
   v
Candidate matching, ranking, reports and schedule data
```

The application stores runtime data locally. Generated databases and local environment files are intentionally excluded from Git.

## Requirements

- Python 3.13 recommended (the project test suite was run using Python 3.13.14)
- Node.js and npm
- Git
- Optional: [Ollama](https://ollama.com/) and a locally installed model for AI assistant, voice-recruiter, and agent features

## Setup and run (Windows PowerShell)

Clone the repository and switch to V2:

```powershell
git clone https://github.com/koppojurahul3-bit/AI_Recruitment_Assistant.git
cd AI_Recruitment_Assistant
git switch v2-development
```

Create and activate a Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

### Start the API

In the project root, run:

```powershell
python -m uvicorn api_server:app --host 127.0.0.1 --port 8765
```

The API documentation is available locally at [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs).

### Start the frontend

Open a second terminal, activate the same virtual environment only if needed for your workflow, then run:

```powershell
cd frontend
npm run dev
```

Open the local URL printed by Vite (typically http://localhost:5173). The frontend defaults to the API at `http://127.0.0.1:8765`. To override it, create `frontend/.env.local` with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8765
```

Do not commit local environment files or secrets.

### Optional: enable Ollama features

Install and start Ollama, then make sure the model you configure is available locally. The API defaults to `OLLAMA_URL=http://127.0.0.1:11434` and `OLLAMA_MODEL=llama3.2:latest`. These can be overridden with environment variables before starting the API. Ollama is not required for every resume-analysis or reporting workflow, but AI-assisted endpoints need it.

## Tests

Activate the project virtual environment and run from the repository root:

```powershell
python -m pytest -q
```

**Latest local verification:** 258 tests passed. Test results describe the local development environment; run the suite in your own environment to verify your setup.

## Project structure

```text
AI_Recruitment_Assistant/
├── analyzer.py
├── api_server.py
├── streamlit_app.py
├── backend/
│   ├── repositories/
│   └── services/
├── tests/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## Security and data notes

- Keep `.env` files, API credentials, uploaded resumes, and generated databases out of version control.
- Resume documents may contain personal information. Use synthetic or consented data when testing and avoid publishing real candidate information.
- This is a decision-support tool. Recruiters should independently review candidate information and make hiring decisions; automated scores should not be treated as the sole basis for employment decisions.

## Roadmap

- Deploy a public V2 demo with documented configuration
- Add screenshots and a short product walkthrough
- Continue improving automated integration coverage and setup documentation

## Author

Rahul — [GitHub profile](https://github.com/koppojurahul3-bit)

---

V2 source: [`v2-development` branch](https://github.com/koppojurahul3-bit/AI_Recruitment_Assistant/tree/v2-development)
