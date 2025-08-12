import os
import structlog
import asyncio


logger = structlog.get_logger()

async def detailed_health_check():
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "service": "BI Self-Service Chatbot",
        "version": "1.0.0",
        "components": {}
    }
    
    try:
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", None)
        # Check OpenAI API (if configured)
        if OPENAI_API_KEY:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=OPENAI_API_KEY)
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
    
if __name__ == "__main__":
    result = asyncio.run(detailed_health_check())
    print(result)