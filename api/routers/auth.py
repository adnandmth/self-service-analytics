"""
Authentication router for the chatbot
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pydantic import BaseModel
import structlog
from sqlalchemy import text

from api.utils.password_utils import verify
from api.utils.oauth2 import create_access_token
import api.core.database as db

logger = structlog.get_logger()
router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

@router.post("/login", response_model=LoginResponse)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint"""
    
    logger.info(f"Login attempt for user: {user_credentials.username}")
    
    fetch_query = text("""
        SELECT id::text, email, password
        FROM public.toba_users
        WHERE LOWER(email) = LOWER(:email)
        LIMIT 1
    """)
    
    async with db.async_engine.begin() as conn:
        result = await conn.execute(fetch_query, {"email": user_credentials.username})
        user = result.mappings().fetchone()
    
    # Step 2: If user is not found, log and return an error
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials"
        )
        
    # Step 3: Validate password using utils.verify
    if not verify(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials"
        )
    
    # Step 4: Generate JWT token with user ID as payload
    generated_token = create_access_token(data = {"user_id": user["id"]})
    
    logger.info(
        "Login successful",
        token=generated_token
    )
    
    return LoginResponse(
        access_token=generated_token,
        user_id=user["id"]
    )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    # In production, invalidate the token
    return {"message": "Logged out successfully"}