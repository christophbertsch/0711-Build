from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class RunCreateRequest(BaseModel):
    project_id: str
    compiled_prompt: str
    repository: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RunResponse(BaseModel):
    run_id: str
    status: str
    percent: int = 0
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class RunCreateResponse(BaseModel):
    run_id: str
    status: str

class HealthResponse(BaseModel):
    ok: bool
    openhands: str
    openhands_healthy: bool = False

class ArtifactResponse(BaseModel):
    id: str
    run_id: str
    type: str
    url: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class RunDetailResponse(RunResponse):
    artifacts: list[ArtifactResponse] = []
    raw: Optional[Dict[str, Any]] = None