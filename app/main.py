import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import get_db, init_db
from .models import Run, Artifact
from .services.orchestrator import start_run
from .services.artifacts import get_run_artifacts
from .clients.openhands import health_check
from .webhooks.github import handle_github_webhook
from .schemas import (
    RunCreateRequest, 
    RunCreateResponse, 
    RunResponse, 
    RunDetailResponse,
    HealthResponse,
    ArtifactResponse
)
from .config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting 0711 OpenHands Runner")
    init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down 0711 OpenHands Runner")

app = FastAPI(
    title="0711 OpenHands Runner",
    description="Standalone service for managing OpenHands conversations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    openhands_healthy = await health_check()
    return HealthResponse(
        ok=True,
        openhands=settings.openhands_base_url,
        openhands_healthy=openhands_healthy
    )

@app.post("/runs", response_model=RunCreateResponse)
async def create_run(
    request: RunCreateRequest,
    db: Session = Depends(get_db)
):
    """Start a new OpenHands run"""
    try:
        run = await start_run(
            db=db,
            project_id=request.project_id,
            compiled_prompt=request.compiled_prompt,
            repository=request.repository,
            metadata=request.metadata
        )
        
        return RunCreateResponse(
            run_id=run.id,
            status=run.status
        )
        
    except Exception as e:
        logger.error(f"Error creating run: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get run status"""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return RunResponse(
        run_id=run.id,
        status=run.status,
        percent=run.percent,
        created_at=run.created_at,
        updated_at=run.updated_at,
        metadata=run.run_metadata
    )

@app.get("/runs/{run_id}/detail", response_model=RunDetailResponse)
async def get_run_detail(run_id: str, db: Session = Depends(get_db)):
    """Get detailed run information including artifacts"""
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    artifacts = get_run_artifacts(db, run_id)
    
    return RunDetailResponse(
        run_id=run.id,
        status=run.status,
        percent=run.percent,
        created_at=run.created_at,
        updated_at=run.updated_at,
        metadata=run.run_metadata,
        raw=run.raw,
        artifacts=[
            ArtifactResponse(
                id=artifact.id,
                run_id=artifact.run_id,
                type=artifact.type,
                url=artifact.url,
                content=artifact.content,
                created_at=artifact.created_at
            )
            for artifact in artifacts
        ]
    )

@app.get("/runs", response_model=list[RunResponse])
async def list_runs(
    project_id: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List runs with optional filtering"""
    query = db.query(Run)
    
    if project_id:
        query = query.filter(Run.project_id == project_id)
    
    if status:
        query = query.filter(Run.status == status)
    
    runs = query.order_by(Run.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        RunResponse(
            run_id=run.id,
            status=run.status,
            percent=run.percent,
            created_at=run.created_at,
            updated_at=run.updated_at,
            metadata=run.run_metadata
        )
        for run in runs
    ]

@app.post("/webhooks/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub webhooks"""
    try:
        return await handle_github_webhook(request, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling GitHub webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.log_level.lower()
    )