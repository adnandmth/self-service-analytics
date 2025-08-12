"""
LLM Service for natural language to SQL conversion
"""

import json
import asyncio
from typing import Dict, List, Optional
import openai
from openai import AsyncOpenAI
import structlog

from api.core.config import settings
from api.utils.cache import get_cache, set_cache

logger = structlog.get_logger()

class LLMService:
    """Service for LLM-based SQL generation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for SQL generation"""
        return """You are a SQL expert assistant for a real estate business intelligence database. 

Your task is to convert natural language queries into safe, read-only SQL queries.

DATABASE SCHEMA:
The database contains the following schemas and tables:

1. dbt_reports schema (Business Intelligence reports):
   - olx: revenues olx contains transactions made in the OLX platform

   
IMPORTANT RULES:
1. ONLY generate SELECT queries - no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER
2. Always use proper table aliases for readability
3. Include appropriate WHERE clauses for date filtering when time periods are mentioned
4. Use LIMIT clauses for large result sets (default 100 rows)
5. Use proper JOIN syntax when combining data from multiple tables
6. Handle date ranges appropriately (last week, this month, etc.)
7. Use aggregate functions (COUNT, SUM, AVG) when counting or summarizing is requested
8. Always specify schema names (bi_reports., dwh_aggregate., dwh_metadata.)

EXAMPLE QUERIES:
- "Show me user leads for last month" → SELECT * FROM bi_reports.users WHERE date >= CURRENT_DATE - INTERVAL '1 month' LIMIT 100
- "Top 10 projects by leads" → SELECT project_name, SUM(leads_30d) as total_leads FROM bi_reports.performance_projects GROUP BY project_name ORDER BY total_leads DESC LIMIT 10
- "Leads by marketing channel" → SELECT marketing_channel, COUNT(*) as lead_count FROM bi_reports.users WHERE date >= CURRENT_DATE - INTERVAL '7 days' GROUP BY marketing_channel

Return ONLY the SQL query, no explanations or additional text."""

    async def generate_sql(
        self, 
        user_query: str, 
        schema_info: Dict,
        conversation_id: Optional[str] = None
    ) -> str:
        """Generate SQL from natural language query"""
        
        # Check cache first
        cache_key = f"sql_generation:{hash(user_query)}"
        cached_result = await get_cache(cache_key)
        if cached_result:
            logger.info("Using cached SQL generation result")
            return cached_result
        
        try:
            # Build context with schema information
            schema_context = self._build_schema_context(schema_info)
            
            # Create messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt + "\n\n" + schema_context},
                {"role": "user", "content": user_query}
            ]
            
            # Add conversation history if available
            if conversation_id:
                history = await self._get_conversation_history(conversation_id)
                if history:
                    messages = history + messages
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
                stop=None
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Cache the result
            await set_cache(cache_key, sql_query, expire=3600)  # 1 hour
            
            logger.info("SQL generated successfully", query=user_query, sql=sql_query)
            return sql_query
            
        except Exception as e:
            logger.error("Failed to generate SQL", error=str(e), query=user_query)
            raise ValueError(f"Failed to generate SQL: {str(e)}")
    
    def _build_schema_context(self, schema_info: Dict) -> str:
        """Build schema context for LLM"""
        context = "CURRENT DATABASE SCHEMA:\n"
        
        for schema_name, schema_data in schema_info.items():
            context += f"\n{schema_name} schema:\n"
            for table_name, table_data in schema_data.get("tables", {}).items():
                context += f"  - {table_name}: {table_data.get('description', '')}\n"
                columns = table_data.get("columns", {})
                if columns:
                    context += f"    Columns: {', '.join(columns.keys())}\n"
        
        return context
    
    async def _get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history for context"""
        try:
            history_data = await get_cache(f"conversation:{conversation_id}")
            if history_data:
                return json.loads(history_data)
        except Exception as e:
            logger.warning("Failed to get conversation history", error=str(e))
        
        return []
    
    async def _save_conversation_history(self, conversation_id: str, messages: List[Dict]):
        """Save conversation history"""
        try:
            # Keep only last 5 exchanges to avoid token limits
            if len(messages) > 10:
                messages = messages[-10:]
            
            await set_cache(
                f"conversation:{conversation_id}",
                json.dumps(messages),
                expire=3600  # 1 hour
            )
        except Exception as e:
            logger.warning("Failed to save conversation history", error=str(e))
    
    async def explain_query(self, sql_query: str) -> str:
        """Explain what a SQL query does in natural language"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Explain what the following SQL query does in simple, non-technical language."},
                    {"role": "user", "content": f"Explain this SQL query: {sql_query}"}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("Failed to explain query", error=str(e))
            return "Unable to explain this query."
    
    async def suggest_improvements(self, user_query: str, sql_query: str) -> List[str]:
        """Suggest improvements to the query"""
        try:
            response = await self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Suggest 2-3 improvements for the given SQL query. Return as a JSON array of strings."},
                    {"role": "user", "content": f"Original question: {user_query}\nSQL query: {sql_query}\nSuggest improvements:"}
                ],
                max_tokens=300,
                temperature=0.2
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            try:
                suggestions = json.loads(suggestions_text)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                # Fallback: split by newlines
                return [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                
        except Exception as e:
            logger.error("Failed to suggest improvements", error=str(e))
            return [] 