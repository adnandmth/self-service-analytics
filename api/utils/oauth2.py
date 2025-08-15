from jose import JWTError, jwt
from datetime import timezone, datetime, timedelta
from fastapi import status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from api.core.config import settings
import structlog

import api.core.database as db

logger = structlog.get_logger()

"""
Defining oauth scheme for user login and access;
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class TokenData(BaseModel):
    id: Optional[str] = None  # ID might be missing if token is invalid


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
     
    logger.info(
        "JWT token created",
        expiration=expire.isoformat(),
        expires_in_minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail=f"could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    token = verify_access_token(token, credentials_exception)
    
    # Fetch user using raw SQL query
    fetch_query = text("""
        SELECT id, email
        FROM public.toba_users
        WHERE id::text = :user_id
        LIMIT 1
    """)
    
    async with db.async_engine.begin() as conn:
        result = await conn.execute(fetch_query, {"user_id": token.id})
        user = result.mappings().fetchone()
        
    if not user:
        raise credentials_exception
     
    return user

def verify_access_token(token: str, credentials_exception):
    try:
        # decode the payload included in the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id") # user_id from pydantic model
        if user_id is None:
            raise credentials_exception

        id = str(user_id)
        token_data = TokenData(id=id)
    except JWTError:
        raise credentials_exception
    
    return token_data


