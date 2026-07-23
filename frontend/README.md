# rag-frontend (Marginal)

React + TypeScript frontend for the AI Research Assistant, built with
Vite. Talks only to the Spring Boot backend — never directly to the
FastAPI AI service.

## Prerequisites

- Node.js 18+
- The Spring Boot backend running on `http://localhost:8080` (which in
  turn needs the FastAPI AI service + Ollama running)

## Setup

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if your backend isn't on :8080
npm run dev
```

Opens on `http://localhost:3000`. Make sure the Spring Boot backend's
CORS config (`SecurityConfig.java`) allows this origin — it already
does by default.

## Build

```bash
npm run build
```

Type-checks with `tsc -b` then bundles with Vite into `dist/`.

## What's here

- **Auth** (`context/AuthContext.tsx`) — JWT stored in memory + persisted
  to `localStorage` so a refresh doesn't log you out. Every API call
  goes through the shared `axios` instance in `api/client.ts`, which
  attaches the token automatically.
- **Document sidebar** (`components/DocumentSidebar.tsx`) — import
  (PDF/DOCX/TXT), see status (`PROCESSING` / `READY` / `FAILED`) and
  chunk count, delete.
- **Chat** (`components/ChatPanel.tsx`) — ask a question, see the
  answer plus a row of citation chips (filename + page) underneath.

## Known gaps (matches the backend's current state)

- No summarization, conversation history, or PDF export yet (section
  6.2 bonus features — not built on either side yet).
- No pagination on the document list — fine at demo scale, would need
  addressing before this holds hundreds of documents per user.
