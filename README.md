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


## Phase 3 — local clip renderer

The Windows local worker now includes `clip_factory.py`. It only processes files placed manually in your local inbox; it never downloads footage from YouTube.

1. Install FFmpeg and ensure `ffmpeg` and `ffprobe` work from PowerShell.
2. Create `media/inbox/my-session/` and put one rights-cleared video in it, for example `source.mp4`.
3. Add `rights_manifest.json` beside the video:
```json
{
  "status": "verified",
  "rights_holder": "Name of rights holder",
  "evidence_reference": "Written permission or license reference",
  "source_file": "source.mp4",
  "editing_allowed": true,
  "derivative_allowed": true,
  "distribution_allowed": true,
  "commercial_allowed": false,
  "attribution_required": true
}
```
4. From `local-worker`, run a dry-run first:
```powershell
py clip_factory.py --inbox ..\\media\\inbox --output ..\\media\\ready
```
5. After checking the planned time ranges and rights, render draft vertical clips:
```powershell
py clip_factory.py --inbox ..\\media\\inbox --output ..\\media\\ready --process
```
Add `--commercial` only when your license explicitly grants commercial use. The renderer makes 1080x1920 drafts with blurred side fill and selects candidate windows using a basic audio-intensity heuristic. It is not yet AI gameplay understanding; inspect each clip. It does not upload.

The manifest is an operator declaration, not independent license validation. Keep the actual permission evidence and review it yourself. YouTube publishing remains disabled.
