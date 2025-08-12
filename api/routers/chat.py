"""
Chat router for natural language query processing
"""

import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog

from api.core.database import execute_query, get_schema_info, validate_table_access
from api.core.config import settings
from api.services.llm_service import LLMService
from api.services.query_validator import QueryValidator
from api.utils.cache import get_cache, set_cache
from api.utils.rate_limiter import check_rate_limit

logger = structlog.get_logger()

router = APIRouter()

# Initialize services
llm_service = LLMService()
query_validator = QueryValidator()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    sql_query: Optional[str] = None
    results: Optional[Dict] = None
    error: Optional[str] = None
    conversation_id: str
    timestamp: str

@router.post("/query", response_model=ChatResponse)
async def process_query(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(lambda: {"id": "test_user"})  # Placeholder
):
    """Process natural language query and return results"""
    
    # Rate limiting
    user_id = current_user.get("id", "anonymous")
    if not await check_rate_limit(user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    try:
        # Get conversation context
        conversation_id = request.conversation_id or f"conv_{user_id}_{asyncio.get_event_loop().time()}"
        
        # Get schema information for LLM context
        schema_info = await get_schema_info()
        
        # Generate SQL from natural language
        sql_query = await llm_service.generate_sql(
            user_query=request.message,
            schema_info=schema_info,
            conversation_id=conversation_id
        )
        
        # Validate generated SQL
        validation_result = await query_validator.validate_query(sql_query)
        if not validation_result["is_valid"]:
            return ChatResponse(
                message=f"I couldn't generate a valid query for your request. {validation_result['error']}",
                conversation_id=conversation_id,
                timestamp=asyncio.get_event_loop().time()
            )
        
        # Execute query
        results = await execute_query(sql_query, limit=settings.MAX_RESULT_ROWS)
        
        # Format response message
        response_message = format_response_message(request.message, results)
        
        # Log query for analytics
        background_tasks.add_task(
            log_query_analytics,
            user_id=user_id,
            original_query=request.message,
            sql_query=sql_query,
            results=results
        )
        
        return ChatResponse(
            message=response_message,
            sql_query=sql_query,
            results=results,
            conversation_id=conversation_id,
            timestamp=str(asyncio.get_event_loop().time())
        )
        
    except Exception as e:
        logger.error("Query processing failed", error=str(e), user_id=user_id)
        return ChatResponse(
            message=f"Sorry, I encountered an error processing your query: {str(e)}",
            error=str(e),
            conversation_id=conversation_id,
            timestamp=asyncio.get_event_loop().time()
        )

@router.get("/schema")
async def get_available_schemas():
    """Get available database schemas and tables"""
    try:
        schema_info = await get_schema_info()
        return {
            "success": True,
            "schemas": schema_info
        }
    except Exception as e:
        logger.error("Failed to get schema info", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get schema information")

@router.get("/sample/{schema}/{table}")
async def get_table_sample_data(schema: str, table: str, limit: int = 5):
    """Get sample data from a specific table"""
    try:
        # Validate table access
        if not validate_table_access(table, schema):
            raise HTTPException(status_code=403, detail="Access to this table is not allowed")
        
        from api.core.database import get_table_sample
        results = await get_table_sample(table, schema, limit)
        return results
        
    except Exception as e:
        logger.error("Failed to get sample data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get sample data")

@router.get("/schema/{schema}/{table}")
async def get_table_schema_info(schema: str, table: str):
    """Get schema information for a specific table"""
    try:
        # Validate table access
        if not validate_table_access(table, schema):
            raise HTTPException(status_code=403, detail="Access to this table is not allowed")
        
        from api.core.database import get_table_schema
        results = await get_table_schema(table, schema)
        return results
        
    except Exception as e:
        logger.error("Failed to get table schema", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get table schema")

def format_response_message(original_query: str, results: Dict) -> str:
    """Format response message based on results"""
    if not results.get("success"):
        return "Sorry, I couldn't retrieve the data you requested."
    
    row_count = results.get("row_count", 0)
    columns = results.get("columns", [])
    
    if row_count == 0:
        return "I found no results matching your query."
    
    # Create a summary based on the original query
    if "count" in original_query.lower() or "how many" in original_query.lower():
        return f"I found {row_count} records matching your query."
    elif "top" in original_query.lower() or "best" in original_query.lower():
        return f"Here are the top {row_count} results:"
    else:
        return f"I found {row_count} records. Here are the results:"

async def log_query_analytics(
    user_id: str,
    original_query: str,
    sql_query: str,
    results: Dict
):
    """Log query analytics for monitoring"""
    try:
        # This would typically go to a logging service or database
        logger.info(
            "Query executed",
            user_id=user_id,
            original_query=original_query,
            sql_query=sql_query,
            row_count=results.get("row_count", 0),
            success=results.get("success", False)
        )
    except Exception as e:
        logger.error("Failed to log query analytics", error=str(e)) 