"""
Authentication router for the chatbot
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime
import structlog
from sqlalchemy import text

from api.utils.password_utils import hash
import api.core.database as db

logger = structlog.get_logger()
router = APIRouter()

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    
class UserCreate(BaseModel):
    email: EmailStr 
    password: str


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def create_user(request: UserCreate):
    # hash the password from user.password
    hashed_password = hash(request.password)
    
    check_query = text("""
        SELECT id FROM public.toba_users WHERE email = :email
    """)
    
    insert_query = text("""
        INSERT INTO public.toba_users (email, password)
        VALUES (:email, :password)
        RETURNING id, email, created_at
    """)
    
    try:
        async with db.async_engine.begin() as conn:
            # 1. Check if email already exists
            result = await conn.execute(check_query, {"email": request.email})
            if result.first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

            # 2. Insert new user
            result = await conn.execute(insert_query, {
                "email": request.email,
                "password": hashed_password
            })

            # 3. Fetch newly created user
            user_row = result.mappings().fetchone()

        return user_row

    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI can handle them
        raise
    except Exception as e:
        logger.error("Failed to create user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the user"
        )