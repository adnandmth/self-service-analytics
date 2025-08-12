"""
Security utilities for authentication and authorization
"""

from typing import Optional, Dict
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

logger = structlog.get_logger()

# Simple token-based auth for now
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict:
    """Get current user from token"""
    if not credentials:
        # For development, allow anonymous access
        return {"user_id": "anonymous", "role": "user"}
    
    token = credentials.credentials
    
    # Simple token validation (replace with proper JWT validation)
    if not token.startswith("token_"):
        # For development, allow access with any token
        return {"user_id": "user", "role": "user"}
    
    try:
        user_id = token.split("_")[1]
        return {
            "user_id": user_id,
            "role": "user"  # In production, get from token claims
        }
    except IndexError:
        # For development, allow access even with invalid token format
        return {"user_id": "user", "role": "user"}

def require_admin(user: Dict = Depends(get_current_user)) -> Dict:
    """Require admin role"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def require_authenticated(user: Dict = Depends(get_current_user)) -> Dict:
    """Require authenticated user"""
    if not user or user.get("user_id") == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    return user 