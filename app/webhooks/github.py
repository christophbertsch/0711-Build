import hashlib
import hmac
import json
import logging
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from ..config import settings
from ..models import Run, RunStatus
from ..services.artifacts import create_pr_artifact

logger = logging.getLogger(__name__)

def verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature"""
    if not settings.github_webhook_secret:
        logger.warning("GitHub webhook secret not configured, skipping signature verification")
        return True
    
    expected_signature = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

async def handle_github_webhook(request: Request, db: Session):
    """Handle GitHub webhook events"""
    # Get signature from headers
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Get payload
    payload = await request.body()
    
    # Verify signature
    if not verify_github_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = request.headers.get("X-GitHub-Event")
    logger.info(f"Received GitHub webhook: {event_type}")
    
    if event_type == "pull_request":
        await handle_pull_request_event(data, db)
    else:
        logger.info(f"Ignoring GitHub event: {event_type}")
    
    return {"status": "ok"}

async def handle_pull_request_event(data: dict, db: Session):
    """Handle GitHub pull request events"""
    action = data.get("action")
    if action not in ["opened", "synchronize"]:
        logger.info(f"Ignoring PR action: {action}")
        return
    
    pr = data.get("pull_request", {})
    pr_url = pr.get("html_url")
    pr_number = pr.get("number")
    repo_name = data.get("repository", {}).get("full_name")
    
    logger.info(f"Processing PR #{pr_number} in {repo_name}: {action}")
    
    # Look for runs that might be associated with this PR
    # This is a simple implementation - you might want more sophisticated matching
    branch_name = pr.get("head", {}).get("ref")
    
    # Find runs that might be related to this PR
    # You could match by branch name, commit SHA, or other metadata
    runs = db.query(Run).filter(
        Run.status.in_([RunStatus.RUNNING.value, RunStatus.STARTED.value])
    ).all()
    
    for run in runs:
        # Simple matching logic - you might want to improve this
        if should_complete_run_for_pr(run, pr, data):
            # Mark run as completed
            run.status = RunStatus.COMPLETED.value
            run.percent = 100
            
            # Create PR artifact
            create_pr_artifact(
                db=db,
                run_id=run.id,
                pr_url=pr_url,
                pr_data={
                    "number": pr_number,
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "repository": repo_name,
                    "branch": branch_name,
                    "action": action
                }
            )
            
            logger.info(f"Marked run {run.id} as completed due to PR #{pr_number}")
    
    db.commit()

def should_complete_run_for_pr(run: Run, pr: dict, webhook_data: dict) -> bool:
    """Determine if a run should be marked complete based on PR data"""
    # This is a simple implementation - you might want more sophisticated logic
    # For example, you could:
    # - Match by commit SHA
    # - Match by branch name in run metadata
    # - Match by repository in run metadata
    # - Use custom tags or identifiers
    
    if not run.run_metadata:
        return False
    
    # Example: match by repository if stored in metadata
    run_repo = run.run_metadata.get("repository")
    pr_repo = webhook_data.get("repository", {}).get("full_name")
    
    if run_repo and pr_repo and run_repo == pr_repo:
        return True
    
    # Example: match by branch name if stored in metadata
    run_branch = run.run_metadata.get("branch")
    pr_branch = pr.get("head", {}).get("ref")
    
    if run_branch and pr_branch and run_branch == pr_branch:
        return True
    
    return False