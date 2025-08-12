"""
Rate limiting utilities for the chatbot API
"""

import asyncio
from typing import Dict
import structlog

from api.core.config import settings
from api.utils.cache import increment_rate_limit, get_rate_limit_count

logger = structlog.get_logger()

async def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit"""
    try:
        current_count = await increment_rate_limit(user_id)
        limit = settings.RATE_LIMIT_PER_MINUTE
        
        if current_count > limit:
            logger.warning("Rate limit exceeded", user_id=user_id, count=current_count, limit=limit)
            return False
        
        return True
        
    except Exception as e:
        logger.error("Rate limit check failed", user_id=user_id, error=str(e))
        # Allow request if rate limiting fails
        return True

async def get_user_rate_limit_status(user_id: str) -> Dict:
    """Get current rate limit status for user"""
    try:
        current_count = await get_rate_limit_count(user_id)
        limit = settings.RATE_LIMIT_PER_MINUTE
        
        return {
            "user_id": user_id,
            "current_count": current_count,
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "exceeded": current_count >= limit
        }
        
    except Exception as e:
        logger.error("Rate limit status check failed", user_id=user_id, error=str(e))
        return {
            "user_id": user_id,
            "current_count": 0,
            "limit": settings.RATE_LIMIT_PER_MINUTE,
            "remaining": settings.RATE_LIMIT_PER_MINUTE,
            "exceeded": False
        }

class RateLimitMiddleware:
    """Middleware for rate limiting requests"""
    
    def __init__(self, rate_limit_per_minute: int = None):
        self.rate_limit = rate_limit_per_minute or settings.RATE_LIMIT_PER_MINUTE
    
    async def __call__(self, request, call_next):
        # Extract user ID from request (implement based on your auth system)
        user_id = self._extract_user_id(request)
        
        # Check rate limit
        if not await check_rate_limit(user_id):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Maximum {self.rate_limit} requests per minute."
            )
        
        # Continue with request
        response = await call_next(request)
        return response
    
    def _extract_user_id(self, request) -> str:
        """Extract user ID from request"""
        # This should be implemented based on your authentication system
        # For now, use IP address as fallback
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}" 