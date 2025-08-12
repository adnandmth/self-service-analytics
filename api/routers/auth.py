"""
Authentication router for the chatbot
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import structlog

from api.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

# Simple token-based auth for now
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str

# Placeholder user database (replace with real auth system)
USERS = {
    "admin": {
        "password": "admin",  # In production, use hashed passwords
        "user_id": "admin",
        "role": "admin"
    },
    "user": {
        "password": "user",
        "user_id": "user", 
        "role": "user"
    }
}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login endpoint"""
    user = USERS.get(request.username)
    
    if not user or user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # In production, generate proper JWT tokens
    token = f"token_{user['user_id']}_{hash(request.username)}"
    
    logger.info("User logged in", user_id=user["user_id"])
    
    return LoginResponse(
        access_token=token,
        user_id=user["user_id"]
    )

@router.get("/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information"""
    # Simple token validation (replace with proper JWT validation)
    token = credentials.credentials
    
    if not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Extract user ID from token
    try:
        user_id = token.split("_")[1]
        return {
            "user_id": user_id,
            "role": "user"  # In production, get from token claims
        }
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    # In production, invalidate the token
    return {"message": "Logged out successfully"}

# Dependency for getting current user
async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for getting current user"""
    token = credentials.credentials
    
    if not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        user_id = token.split("_")[1]
        return {
            "user_id": user_id,
            "role": "user"
        }
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format") 