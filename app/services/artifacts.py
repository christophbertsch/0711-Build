import logging
from sqlalchemy.orm import Session
from ..models import Artifact

logger = logging.getLogger(__name__)

def create_artifact(
    db: Session,
    run_id: str,
    artifact_type: str,
    url: str | None = None,
    content: dict | None = None
) -> Artifact:
    """Create a new artifact for a run"""
    artifact = Artifact(
        run_id=run_id,
        type=artifact_type,
        url=url,
        content=content
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    
    logger.info(f"Created artifact {artifact.id} for run {run_id}")
    return artifact

def get_run_artifacts(db: Session, run_id: str) -> list[Artifact]:
    """Get all artifacts for a run"""
    return db.query(Artifact).filter(Artifact.run_id == run_id).all()

def create_pr_artifact(db: Session, run_id: str, pr_url: str, pr_data: dict) -> Artifact:
    """Create a PR artifact"""
    return create_artifact(
        db=db,
        run_id=run_id,
        artifact_type="pr",
        url=pr_url,
        content=pr_data
    )

def create_file_artifact(db: Session, run_id: str, file_path: str, file_content: str) -> Artifact:
    """Create a file artifact"""
    return create_artifact(
        db=db,
        run_id=run_id,
        artifact_type="file",
        content={"path": file_path, "content": file_content}
    )

def create_log_artifact(db: Session, run_id: str, log_data: dict) -> Artifact:
    """Create a log artifact"""
    return create_artifact(
        db=db,
        run_id=run_id,
        artifact_type="log",
        content=log_data
    )