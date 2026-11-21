from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .config import settings
from .database import Base, engine, get_db
from .models import ChannelTarget, SourcePermission, Worker, ProcessingJob
from .schemas import WorkerHeartbeat, PermissionCreate, PermissionVerify

Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.allowed_origins.split(",")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return {
        "channels": db.scalar(select(func.count()).select_from(ChannelTarget)) or 0,
        "permissions_pending": db.scalar(select(func.count()).select_from(SourcePermission).where(SourcePermission.status == "pending")) or 0,
        "permissions_verified": db.scalar(select(func.count()).select_from(SourcePermission).where(SourcePermission.status == "verified")) or 0,
        "jobs_queued": db.scalar(select(func.count()).select_from(ProcessingJob).where(ProcessingJob.status == "queued")) or 0,
        "workers_online": db.scalar(select(func.count()).select_from(Worker).where(Worker.status == "online")) or 0,
        "publishing_enabled": False,
        "daily_target": 5
    }

@app.post("/api/channels/seed")
def seed_channel(db: Session = Depends(get_db)):
    channel_id = "UCX8pnu3DYUnx8qy8V_c6oHg"
    item = db.scalar(select(ChannelTarget).where(ChannelTarget.channel_id == channel_id))
    if not item:
        item = ChannelTarget(channel_id=channel_id, channel_url=f"https://www.youtube.com/channel/{channel_id}", display_name=None)
        db.add(item)
        db.commit()
        db.refresh(item)
    return {"id": item.id, "channel_id": item.channel_id, "status": "monitoring_target_saved"}

@app.post("/api/workers/heartbeat")
def worker_heartbeat(data: WorkerHeartbeat, db: Session = Depends(get_db)):
    item = db.scalar(select(Worker).where(Worker.worker_id == data.worker_id))
    now = datetime.now(timezone.utc)
    if item is None:
        item = Worker(worker_id=data.worker_id)
        db.add(item)
    item.hostname = data.hostname
    item.version = data.version
    item.status = "online"
    item.last_seen_at = now
    db.commit()
    return {"accepted": True, "worker_id": item.worker_id, "last_seen_at": now.isoformat()}

@app.post("/api/permissions")
def create_permission(data: PermissionCreate, db: Session = Depends(get_db)):
    if db.scalar(select(SourcePermission).where(SourcePermission.video_id == data.video_id)):
        raise HTTPException(409, "A permission record already exists for this video.")
    item = SourcePermission(**data.model_dump(), status="pending")
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "video_id": item.video_id, "status": item.status}

@app.post("/api/permissions/{permission_id}/verify")
def verify_permission(permission_id: int, data: PermissionVerify, db: Session = Depends(get_db)):
    if data.status != "verified":
        raise HTTPException(400, "Only the verified transition is supported here.")
    item = db.get(SourcePermission, permission_id)
    if item is None:
        raise HTTPException(404, "Permission record not found.")
    if not (item.editing_allowed and item.derivative_allowed and item.distribution_allowed):
        raise HTTPException(400, "Cannot verify: editing, derivative-work, and distribution rights must all be explicitly granted.")
    if not item.evidence_reference.strip():
        raise HTTPException(400, "Cannot verify without evidence reference.")
    item.status = "verified"
    item.verified_by = data.verified_by
    item.verified_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": item.id, "status": item.status, "verified_by": item.verified_by}

@app.get("/api/permissions/{video_id}/gate")
def permission_gate(video_id: str, db: Session = Depends(get_db)):
    item = db.scalar(select(SourcePermission).where(SourcePermission.video_id == video_id))
    allowed = bool(item and item.status == "verified" and item.editing_allowed and item.derivative_allowed and item.distribution_allowed)
    return {"video_id": video_id, "processing_allowed": allowed, "reason": "verified_rights" if allowed else "rights_not_verified"}
