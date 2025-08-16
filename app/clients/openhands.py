import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

def _get_headers():
    """Get headers for OpenHands API requests"""
    headers = {"Content-Type": "application/json"}
    if settings.openhands_token:
        headers["Authorization"] = f"Bearer {settings.openhands_token}"
    return headers

async def start_conversation(initial_user_msg: str, repository: str | None = None) -> str:
    """Start a new conversation with OpenHands"""
    payload = {"initial_user_msg": initial_user_msg}
    if repository:
        payload["repository"] = repository
    
    headers = _get_headers()
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            # Try the API endpoint first
            url = f"{settings.openhands_base_url}/api/conversations"
            logger.info(f"Starting conversation at {url}")
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            conv_id = data.get("conversation_id") or data.get("id")
            
            if not conv_id:
                raise ValueError("No conversation ID returned from OpenHands")
                
            logger.info(f"Started conversation with ID: {conv_id}")
            return conv_id
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error starting conversation: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error starting conversation: {str(e)}")
            raise

async def get_conversation(conv_id: str) -> dict:
    """Get conversation status and data"""
    headers = _get_headers()
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            url = f"{settings.openhands_base_url}/api/conversations/{conv_id}"
            logger.debug(f"Getting conversation status from {url}")
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Conversation {conv_id} status: {data.get('status', 'unknown')}")
            return data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting conversation {conv_id}: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting conversation {conv_id}: {str(e)}")
            raise

async def health_check() -> bool:
    """Check if OpenHands instance is healthy"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.openhands_base_url}/health")
            return response.status_code == 200
    except Exception as e:
        logger.error(f"OpenHands health check failed: {str(e)}")
        return False