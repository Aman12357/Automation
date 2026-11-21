from pydantic import BaseModel, Field

class WorkerHeartbeat(BaseModel):
    worker_id: str = Field(min_length=2, max_length=100)
    hostname: str | None = None
    version: str = "0.1.0"

class PermissionCreate(BaseModel):
    video_id: str = Field(min_length=6, max_length=32)
    rights_holder: str
    evidence_reference: str
    editing_allowed: bool = False
    derivative_allowed: bool = False
    distribution_allowed: bool = False
    commercial_allowed: bool = False
    attribution_required: bool = True

class PermissionVerify(BaseModel):
    verified_by: str
    status: str = "verified"
