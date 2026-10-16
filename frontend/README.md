# AI Recruitment Assistant — React frontend

This folder contains the React + Vite interface for V2. It calls the FastAPI service in the repository root.

## Prerequisites

- Node.js and npm
- The FastAPI backend running at `http://127.0.0.1:8765` (unless configured otherwise)

## Install and run

From this directory:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite.

By default, the frontend sends API requests to `http://127.0.0.1:8765`. To use another API address, create a local `.env.local` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8765
```

Do not commit local environment files or secrets.

## Quality checks

```bash
npm run lint
npm run build
```

## Backend

From the repository root, install Python dependencies and start the API:

```bash
python -m pip install -r requirements.txt
python -m uvicorn api_server:app --host 127.0.0.1 --port 8765
```

API documentation: http://127.0.0.1:8765/docs

See the root [README](../README.md) for the complete architecture, setup steps, testing instructions, and data-handling notes.
