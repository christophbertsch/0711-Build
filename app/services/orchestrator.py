import asyncio
import math
import logging
from sqlalchemy.orm import Session
from ..clients.openhands import start_conversation, get_conversation
from ..db import SessionLocal
from ..models import Run, RunStatus
from ..config import settings

logger = logging.getLogger(__name__)

async def poll_until_done(run_id: str, conv_id: str):
    """Poll OpenHands conversation until completion"""
    delay = settings.poll_min_seconds
    logger.info(f"Starting polling for run {run_id}, conversation {conv_id}")
    
    while True:
        try:
            # Get conversation data from OpenHands
            data = await get_conversation(conv_id)
            status = (data.get("status") or "RUNNING").upper()
            
            # Calculate progress based on steps/messages
            steps = data.get("steps") or data.get("messages") or []
            percent = min(95, 5 + 5 * len(steps))
            
            # Update run in database
            with SessionLocal() as db:
                run: Run | None = db.get(Run, run_id)
                if run:
                    run.status = status
                    run.percent = percent
                    run.raw = data
                    db.commit()
                    logger.debug(f"Updated run {run_id}: status={status}, percent={percent}")
                else:
                    logger.error(f"Run {run_id} not found in database")
                    break
            
            # Check if conversation is complete
            if status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value, "CANCELLED"):
                with SessionLocal() as db:
                    run = db.get(Run, run_id)
                    if run:
                        run.percent = 100 if status == RunStatus.COMPLETED.value else run.percent
                        db.commit()
                        logger.info(f"Run {run_id} completed with status {status}")
                break
            
            # Wait before next poll with exponential backoff
            await asyncio.sleep(delay)
            delay = min(math.ceil(delay * 1.5), settings.poll_max_seconds)
            
        except Exception as e:
            logger.error(f"Error polling run {run_id}: {str(e)}")
            # Continue polling on error, but with longer delay
            await asyncio.sleep(settings.poll_max_seconds)

async def start_run(
    db: Session, 
    project_id: str, 
    compiled_prompt: str, 
    repository: str | None = None, 
    metadata: dict | None = None
) -> Run:
    """Start a new OpenHands run"""
    logger.info(f"Starting new run for project {project_id}")
    
    # Create run record
    run = Run(
        project_id=project_id, 
        status=RunStatus.QUEUED.value, 
        run_metadata=metadata
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    
    try:
        # Start OpenHands conversation
        conv_id = await start_conversation(compiled_prompt, repository)
        
        # Update run with conversation ID
        run.conv_id = conv_id
        run.status = RunStatus.STARTED.value
        db.commit()
        db.refresh(run)
        
        # Start polling task
        asyncio.create_task(poll_until_done(run.id, conv_id))
        
        logger.info(f"Started run {run.id} with conversation {conv_id}")
        return run
        
    except Exception as e:
        # Mark run as failed
        run.status = RunStatus.FAILED.value
        run.raw = {"error": str(e)}
        db.commit()
        logger.error(f"Failed to start run {run.id}: {str(e)}")
        raise