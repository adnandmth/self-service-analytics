"""
Structured logging configuration for the chatbot
"""

import sys
import logging
from typing import Any, Dict
import structlog
from structlog.stdlib import LoggerFactory

def setup_logging():
    """Setup structured logging configuration"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, "INFO", logging.INFO)
    )

class ChatbotLogger:
    """Custom logger for chatbot-specific logging"""
    
    def __init__(self, name: str = "chatbot"):
        self.logger = structlog.get_logger(name)
    
    def log_query(self, user_id: str, query: str, sql: str, result_count: int, success: bool):
        """Log query execution"""
        self.logger.info(
            "Query executed",
            user_id=user_id,
            query=query,
            sql=sql,
            result_count=result_count,
            success=success
        )
    
    def log_error(self, user_id: str, error: str, context: Dict[str, Any] = None):
        """Log error with context"""
        log_data = {
            "user_id": user_id,
            "error": error,
            "level": "error"
        }
        if context:
            log_data.update(context)
        
        self.logger.error("Chatbot error", **log_data)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        self.logger.info(
            "Performance metric",
            operation=operation,
            duration_ms=duration * 1000,
            **kwargs
        )
    
    def log_user_activity(self, user_id: str, action: str, **kwargs):
        """Log user activity"""
        self.logger.info(
            "User activity",
            user_id=user_id,
            action=action,
            **kwargs
        )

# Create global logger instance
chatbot_logger = ChatbotLogger() 