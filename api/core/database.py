"""
Database connection and schema management
"""

import asyncio
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from api.core.config import settings, BI_SCHEMA_INFO

logger = structlog.get_logger()

# Database engines
sync_engine = None
async_engine = None
AsyncSessionLocal = None
inspector = None

async def init_db():
    """Initialize database connections"""
    global sync_engine, async_engine, AsyncSessionLocal, inspector
    
    if async_engine is not None:
        return  # Already initialized
    
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.PGDATABASE_HOSTNAME}:{settings.PGDATABASE_PORT}/{settings.PGDATABASE_PANDAWA}"
    
    try:
        # Create async engine for query execution
        async_engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG
        )
        
        AsyncSessionLocal = sessionmaker(
            async_engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create sync engine for schema introspection
        sync_engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DEBUG
        )
        inspector = inspect(sync_engine)
        
        # Test connection
        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("Database connection established successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
"""
This function is intended to be used as a FastAPI dependency that provides a per-request
asynchronous SQLAlchemy session (AsyncSession). It manages the lifecycle of the session,
including committing or rolling back transactions and releasing the connection back to the pool
automatically once the request is completed.

Using this session is most beneficial for endpoints that require transactional consistency
or ORM-related operations, such as creating, updating, or deleting records.
For simple read-only queries, directly using the async_engine for executing raw SQL may be more efficient.
"""
async def get_db_session():
    """Get database session"""
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_connection():
    """Get synchronous database connection"""
    return psycopg2.connect(
        settings.DATABASE_URL,
        cursor_factory=RealDictCursor
    )

async def get_schema_info() -> Dict:
    """Get database schema information for LLM context"""
    schema_info = {}
    
    for schema in settings.BI_SCHEMAS:
        schema_info[schema] = {
            "description": BI_SCHEMA_INFO.get(schema, {}).get("description", ""),
            "tables": {}
        }
        
        try:
            tables = inspector.get_table_names(schema=schema)
            for table in tables:
                columns = inspector.get_columns(table, schema=schema)
                column_info = {col["name"]: col["type"].__class__.__name__ for col in columns}
                
                schema_info[schema]["tables"][table] = {
                    "description": BI_SCHEMA_INFO.get(schema, {}).get("tables", {}).get(table, ""),
                    "columns": column_info
                }
        except Exception as e:
            logger.warning(f"Could not inspect schema {schema}", error=str(e))
    
    return schema_info

async def execute_query(query: str, limit: int = None) -> Dict:
    """Execute SQL query safely"""  
    # Basic query validation
    query = query.strip()
    if not query:
        raise ValueError("Query cannot be empty")
    
    # Check for dangerous operations
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE"]
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"Operation {keyword} is not allowed")
    
    # Add LIMIT if not present and limit is specified
    if limit and "LIMIT" not in query_upper:
        query += f" LIMIT {limit}"
    
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text(query))
            
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                
                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data),
                    "columns": list(columns)
                }
            else:
                return {
                    "success": True,
                    "data": [],
                    "row_count": 0,
                    "columns": [],
                    "message": "Query executed successfully (no results)"
                }
                
    except Exception as e:
        logger.error("Query execution failed", query=query, error=str(e))
        raise ValueError(f"Query execution failed: {str(e)}")

async def get_table_sample(table_name: str, schema: str = "bi_reports", limit: int = 5) -> Dict:
    """Get sample data from a table"""
    query = f"SELECT * FROM {schema}.{table_name} LIMIT {limit}"
    return await execute_query(query)

async def get_table_schema(table_name: str, schema: str = "bi_reports") -> Dict:
    """Get table schema information"""
    query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_schema = '{schema}' 
    AND table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    return await execute_query(query)

def validate_table_access(table_name: str, schema: str = "bi_reports") -> bool:
    """Validate if table is in readonly list"""
    full_table_name = f"{schema}.{table_name}"
    return full_table_name in settings.READONLY_TABLES 