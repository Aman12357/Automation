# GTA Shorts AI Factory — Phase 1

A safe hybrid foundation for monitoring a creator channel, recording source-rights evidence, managing processing jobs, and registering a Windows worker. This phase does **not** download YouTube videos, render clips, or publish uploads.

## Safety model
- YouTube Data API is intended for public channel/playlist metadata only.
- Media ingestion remains disabled until source permission/license evidence is verified.
- The uploader is intentionally not implemented in Phase 1.
- No OAuth tokens or API keys are committed.
- A public video URL is not permission to download or republish footage.

## Stack
- API: FastAPI + SQLAlchemy
- Database: SQLite by default; PostgreSQL via DATABASE_URL
- Dashboard: React + Vite
- Windows worker: Python heartbeat client

## Quick start — API
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000 | Docs: http://127.0.0.1:8000/docs

## Quick start — dashboard
```powershell
cd frontend
npm install
npm run dev
```
Dashboard: http://localhost:5173

## Quick start — local worker
Start the API first:
```powershell
cd local-worker
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:API_BASE_URL="http://127.0.0.1:8000"
$env:WORKER_ID="windows-pc-01"
py worker.py
```

## Creator channel
Configured target: `UCX8pnu3DYUnx8qy8V_c6oHg`.
The supplied URL is a channel URL, not a playlist URL. Public metadata discovery will be
implemented using the official YouTube Data API. Set YOUTUBE_API_KEY in backend/.env when
that integration is added. Do not scrape or bypass access controls.

## Rights workflow
Each source must have a record of the rights holder, evidence reference, editing rights,
derivative-work rights, distribution rights, commercial rights (if monetizing), attribution
requirements, validity dates, and verification status. Processing must remain blocked until
the required rights are explicitly granted and evidence has been checked by a person.

## Phase 1 status
Implemented: health/status API, channel target model, playlist and permission models, job and
worker models, permission gate, worker heartbeat, starter dashboard.
Not implemented: YouTube metadata client, permission review UI, media ingestion, highlight
detection, FFmpeg rendering, YouTube OAuth, uploads, cloud deployment.
