"""
Configuration settings for BI Self-Service Chatbot
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "BI Toba Self-Service Chatbot"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-this"
    
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    PGDATABASE_PANDAWA: str
    PGDATABASE_HOSTNAME: str
    PGDATABASE_PORT: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # OpenAI/LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.1
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str]
    
    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Query settings
    MAX_QUERY_EXECUTION_TIME: int = 300  # seconds
    MAX_RESULT_ROWS: int = 10000
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # BI Schema settings
    BI_SCHEMAS: List[str]
    READONLY_TABLES: List[str]
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v
    
    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError("OPENAI_API_KEY must be set")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Database schema information for LLM context
BI_SCHEMA_INFO = {
    "dbt_reports": {
        "description": "Business Intelligence report tables",
        "tables": {
            "rep_leads": "User leads and interactions"
        }
    }
} 