# LawyerIR SEO OS

An AI-powered SEO management system for [LawyerIR.com](https://lawyerir.com).

## Overview

LawyerIR SEO OS centralizes SEO monitoring, analysis, and optimization for the LawyerIR platform. It combines a FastAPI backend, a React dashboard, PostgreSQL storage, and AI agents for automated insights and reporting.

## Project Structure

```
LawyerIR-SEO-OS/
├── backend/          # FastAPI REST API
├── frontend/         # React dashboard
├── database/         # SQL schema and migrations
├── ai-agent/         # AI prompts, analyzers, and agents
├── reports/          # Generated SEO reports
├── docker/           # Container configuration
└── docs/             # Project documentation
```

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python, FastAPI, Uvicorn |
| Frontend   | React, Vite, TypeScript  |
| Database   | PostgreSQL               |
| AI         | LLM-based agents         |
| DevOps     | Docker, Docker Compose   |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

### Docker (all services)

```bash
cd docker
docker compose up --build
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable            | Description              |
|---------------------|--------------------------|
| `DATABASE_URL`      | PostgreSQL connection    |
| `OPENAI_API_KEY`    | AI provider API key      |
| `LAWYERIR_SITE_URL` | Target site URL          |

## Status

**Foundation phase** — basic project structure and starter code. Advanced features (crawling, ranking tracking, AI reports) are planned for subsequent phases.

## License

Proprietary — LawyerIR.com
