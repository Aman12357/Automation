# GTA Shorts AI Factory — Phase 2

A rights-first hybrid foundation for monitoring a creator channel and preparing authorized GTA Shorts workflows. Phase 2 adds official YouTube Data API metadata discovery and a protected manual rights-verification endpoint.

## Safety model
- YouTube Data API is used for public channel, playlist, and video metadata only.
- This project does not download video/audio, bypass YouTube controls, or extract clips from third-party uploads.
- A public video URL is not permission to download, edit, monetize, or republish footage.
- Rights verification requires a separately configured reviewer token and human evidence review.
- Publishing remains hard-disabled. No YouTube OAuth uploader is included.

## Stack
FastAPI + SQLAlchemy + HTTPX, SQLite by default (PostgreSQL supported), React + Vite dashboard, and a Windows Python heartbeat worker.

## API setup
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Set `YOUTUBE_API_KEY` using a Google Cloud project with YouTube Data API v3 enabled. Set `RIGHTS_REVIEW_TOKEN` to a long random secret. Never commit your real .env file.
```powershell
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

## YouTube metadata endpoints
- `GET /api/youtube/channels/{channel_id}` — public channel metadata and uploads playlist ID.
- `GET /api/youtube/channels/{channel_id}/playlists` — public playlists; optional `page_token`.
- `GET /api/youtube/playlists/{playlist_id}/videos` — public video metadata; optional `page_token`.
- `GET /api/health` — API key and reviewer-token configuration status.

Configured target: `UCX8pnu3DYUnx8qy8V_c6oHg`.

## Rights review
Create a pending record with `POST /api/permissions`. Manually inspect the actual license/permission evidence. Then call `POST /api/permissions/{id}/verify` with header `X-Rights-Review-Token: <your token>` and reviewer name. Editing, derivative-work, distribution permissions, rights-holder and evidence reference are required. The token gates the reviewer action; it does not itself prove a license is valid.

## Dashboard and worker
Dashboard: `cd frontend; npm install; npm run dev`. Start the Windows worker using the existing `local-worker/worker.py` instructions.

## Phase 2 status
Implemented: official YouTube metadata client, channel/playlist/video metadata endpoints, playlist persistence, protected rights-verification transition, rights inventory endpoint, publishing lock.
Not implemented: media ingestion, clipping/highlight detection, FFmpeg rendering, rights-review UI, YouTube OAuth, upload/scheduling, cloud deployment. This is not yet an automated uploader.
