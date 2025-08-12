"""
Health check router for monitoring
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import structlog

from api.core.database import init_db
from api.utils.cache import get_cache_stats
from api.core.config import settings

logger = structlog.get_logger()
router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "BI Self-Service Chatbot",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "service": "BI Self-Service Chatbot",
        "version": "1.0.0",
        "components": {}
    }
    
    try:
        # Check database connection
        try:
            await init_db()
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # Check Redis cache
        try:
            cache_stats = await get_cache_stats()
            if cache_stats:
                health_status["components"]["cache"] = {
                    "status": "healthy",
                    "message": "Cache connection successful",
                    "stats": cache_stats
                }
            else:
                health_status["components"]["cache"] = {
                    "status": "unhealthy",
                    "message": "Cache connection failed"
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "message": f"Cache connection failed: {str(e)}"
            }
            health_status["status"] = "degraded"
        
        # Check OpenAI API (if configured)
        if settings.OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                completion = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "developer", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello!"}
                    ],
                    max_tokens=5
                )

                print(completion.choices[0].message)
                health_status["components"]["openai"] = {
                    "status": "healthy",
                    "message": "OpenAI API connection successful"
                }
            except Exception as e:
                health_status["components"]["openai"] = {
                    "status": "unhealthy",
                    "message": f"OpenAI API connection failed: {str(e)}"
                }
                health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Check if all critical components are ready
        await init_db()
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive"} 