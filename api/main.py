"""
BI Self-Service Chatbot API
Main FastAPI application for natural language query processing
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from api.routers import chat, auth, health, export, user
from api.core.config import settings
from api.core.database import init_db
from api.utils.oauth2 import get_current_user
from api.utils.logging import setup_logging

# Setup structured logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events.
    define logic (code) that should be executed before the application starts up. 
    This means that this code will be executed once, before the application starts receiving requests.
    """
    # Startup
    logger.info("Starting BI Toba Self-Service Chatbot API")
    await init_db()
    logger.info("Database connection established")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BI Self-Service Chatbot API")

# Create FastAPI app
app = FastAPI(
    title="BI Toba: Self-Service Chatbot API",
    description="Natural language query interface for BI report tables",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Include routers
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(
    chat.router, 
    prefix="/api/v1/chat", 
    tags=["chat"]
)
app.include_router(
    export.router, 
    prefix="/api/v1/export", 
    tags=["export"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BI Self-Service Chatbot API",
        "version": "1.0.0",
        "status": "running"
    }