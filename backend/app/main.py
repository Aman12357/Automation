from datetime import datetime, timezone
import secrets
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .config import settings
from .database import Base, engine, get_db
from .models import ChannelTarget, Playlist, SourcePermission, Worker, ProcessingJob
from .schemas import WorkerHeartbeat, PermissionCreate, PermissionVerify
from .youtube import get_channel, list_playlists, list_playlist_videos

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.allowed_origins.split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def require_rights_reviewer(token: str | None):
    expected = settings.rights_review_token
    if not expected:
        raise HTTPException(503, "Rights review is locked. Configure RIGHTS_REVIEW_TOKEN before enabling manual verification.")
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(401, "A valid rights reviewer token is required.")

@app.get("/api/health")
def health():
    return {"status":"ok","service":settings.app_name,"version":"0.2.0",
            "youtube_api_configured":bool(settings.youtube_api_key),
            "rights_review_configured":bool(settings.rights_review_token),
            "publishing_enabled":False}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "channels": db.scalar(select(func.count()).select_from(ChannelTarget)) or 0,
        "permissions_pending": db.scalar(select(func.count()).select_from(SourcePermission).where(SourcePermission.status == "pending")) or 0,
        "permissions_verified": db.scalar(select(func.count()).select_from(SourcePermission).where(SourcePermission.status == "verified")) or 0,
        "jobs_queued": db.scalar(select(func.count()).select_from(ProcessingJob).where(ProcessingJob.status == "queued")) or 0,
        "workers_online": db.scalar(select(func.count()).select_from(Worker).where(Worker.status == "online")) or 0,
        "publishing_enabled": False, "daily_target": 5}

@app.post("/api/channels/seed")
def seed_channel(db: Session = Depends(get_db)):
    channel_id = "UCX8pnu3DYUnx8qy8V_c6oHg"
    item = db.scalar(select(ChannelTarget).where(ChannelTarget.channel_id == channel_id))
    if not item:
        item = ChannelTarget(channel_id=channel_id, channel_url=f"https://www.youtube.com/channel/{channel_id}")
        db.add(item); db.commit(); db.refresh(item)
    return {"id":item.id,"channel_id":item.channel_id,"status":"monitoring_target_saved"}

@app.get("/api/youtube/channels/{channel_id}")
def youtube_channel_metadata(channel_id: str):
    return get_channel(channel_id)

@app.get("/api/youtube/channels/{channel_id}/playlists")
def youtube_channel_playlists(channel_id: str, page_token: str | None = None, db: Session = Depends(get_db)):
    result = list_playlists(channel_id, page_token)
    for item in result["items"]:
        existing = db.scalar(select(Playlist).where(Playlist.playlist_id == item["playlist_id"]))
        if existing is None:
            existing = Playlist(playlist_id=item["playlist_id"], channel_id=channel_id)
            db.add(existing)
        existing.title = item["title"]
        existing.item_count = item["item_count"]
        existing.last_checked_at = datetime.now(timezone.utc)
    db.commit()
    return result

@app.get("/api/youtube/playlists/{playlist_id}/videos")
def youtube_playlist_videos(playlist_id: str, page_token: str | None = None):
    return list_playlist_videos(playlist_id, page_token)

@app.get("/api/permissions")
def list_permissions(db: Session = Depends(get_db)):
    items = db.scalars(select(SourcePermission).order_by(SourcePermission.id.desc())).all()
    return [{"id":x.id,"video_id":x.video_id,"rights_holder":x.rights_holder,
             "evidence_reference":x.evidence_reference,"editing_allowed":x.editing_allowed,
             "derivative_allowed":x.derivative_allowed,"distribution_allowed":x.distribution_allowed,
             "commercial_allowed":x.commercial_allowed,"attribution_required":x.attribution_required,
             "status":x.status,"verified_by":x.verified_by,"verified_at":x.verified_at} for x in items]

@app.post("/api/workers/heartbeat")
def worker_heartbeat(data: WorkerHeartbeat, db: Session = Depends(get_db)):
    item = db.scalar(select(Worker).where(Worker.worker_id == data.worker_id))
    now = datetime.now(timezone.utc)
    if item is None:
        item = Worker(worker_id=data.worker_id); db.add(item)
    item.hostname=data.hostname; item.version=data.version; item.status="online"; item.last_seen_at=now
    db.commit()
    return {"accepted":True,"worker_id":item.worker_id,"last_seen_at":now.isoformat()}

@app.post("/api/permissions")
def create_permission(data: PermissionCreate, db: Session = Depends(get_db)):
    if db.scalar(select(SourcePermission).where(SourcePermission.video_id == data.video_id)):
        raise HTTPException(409,"A permission record already exists for this video.")
    item=SourcePermission(**data.model_dump(),status="pending")
    db.add(item); db.commit(); db.refresh(item)
    return {"id":item.id,"video_id":item.video_id,"status":item.status}

@app.post("/api/permissions/{permission_id}/verify")
def verify_permission(permission_id: int, data: PermissionVerify,
                     x_rights_review_token: str | None = Header(default=None),
                     db: Session = Depends(get_db)):
    require_rights_reviewer(x_rights_review_token)
    if data.status != "verified":
        raise HTTPException(400,"Only the verified transition is supported here.")
    item=db.get(SourcePermission,permission_id)
    if item is None: raise HTTPException(404,"Permission record not found.")
    if not (item.editing_allowed and item.derivative_allowed and item.distribution_allowed):
        raise HTTPException(400,"Cannot verify: editing, derivative-work, and distribution rights must all be explicitly granted.")
    if not item.evidence_reference.strip() or not item.rights_holder.strip():
        raise HTTPException(400,"Cannot verify without a rights holder and evidence reference.")
    item.status="verified"; item.verified_by=data.verified_by
    item.verified_at=datetime.now(timezone.utc); db.commit()
    return {"id":item.id,"status":item.status,"verified_by":item.verified_by}

@app.get("/api/permissions/{video_id}/gate")
def permission_gate(video_id: str, db: Session = Depends(get_db)):
    item=db.scalar(select(SourcePermission).where(SourcePermission.video_id == video_id))
    allowed=bool(item and item.status=="verified" and item.editing_allowed and item.derivative_allowed and item.distribution_allowed)
    return {"video_id":video_id,"processing_allowed":allowed,"reason":"verified_rights" if allowed else "rights_not_verified"}

@app.get("/api/publishing/status")
def publishing_status():
    return {"enabled":False,"reason":"Publishing stays disabled until rights review, processing QA, and YouTube OAuth scopes are implemented."}
