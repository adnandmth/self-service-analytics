"""
Query validation service for SQL safety and correctness
"""

import re
from typing import Dict, List, Tuple
import structlog

from api.core.config import settings

logger = structlog.get_logger()

class QueryValidator:
    """Service for validating SQL queries"""
    
    def __init__(self):
        self.dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", 
            "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "EXEC"
        ]
        
        self.allowed_schemas = settings.BI_SCHEMAS
        self.readonly_tables = settings.READONLY_TABLES
        
        # SQL injection patterns
        self.injection_patterns = [
            r"';.*--",
            r"';.*#",
            r"';.*/\*",
            r"UNION.*SELECT",
            r"OR.*1=1",
            r"OR.*'1'='1'",
            r"AND.*1=1",
            r"AND.*'1'='1'"
        ]
    
    async def validate_query(self, sql_query: str) -> Dict:
        """Validate SQL query for safety and correctness"""
        
        validation_result = {
            "is_valid": True,
            "error": None,
            "warnings": []
        }
        
        try:
            # Basic checks
            if not sql_query or not sql_query.strip():
                validation_result["is_valid"] = False
                validation_result["error"] = "Query cannot be empty"
                return validation_result
            
            # Convert to uppercase for keyword checking
            query_upper = sql_query.upper().strip()
            
            # Check for dangerous operations
            for keyword in self.dangerous_keywords:
                if keyword in query_upper:
                    validation_result["is_valid"] = False
                    validation_result["error"] = f"Operation '{keyword}' is not allowed"
                    return validation_result
            
            # Check for SQL injection patterns
            for pattern in self.injection_patterns:
                if re.search(pattern, query_upper, re.IGNORECASE):
                    validation_result["is_valid"] = False
                    validation_result["error"] = "Query contains potentially malicious patterns"
                    return validation_result
            
            # Validate schema access
            schema_validation = self._validate_schema_access(sql_query)
            if not schema_validation["is_valid"]:
                validation_result["is_valid"] = False
                validation_result["error"] = schema_validation["error"]
                return validation_result
            
            # Check query structure
            structure_validation = self._validate_query_structure(sql_query)
            if not structure_validation["is_valid"]:
                validation_result["warnings"].append(structure_validation["error"])
            
            # Check for reasonable limits
            limit_validation = self._validate_query_limits(sql_query)
            if not limit_validation["is_valid"]:
                validation_result["warnings"].append(limit_validation["error"])
            
            logger.info("Query validation passed", query=sql_query[:100])
            return validation_result
            
        except Exception as e:
            logger.error("Query validation failed", error=str(e), query=sql_query)
            validation_result["is_valid"] = False
            validation_result["error"] = f"Validation error: {str(e)}"
            return validation_result
    
    def _validate_schema_access(self, sql_query: str) -> Dict:
        """Validate that query only accesses allowed schemas and tables"""
        
        # Extract table references from query
        table_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
        table_matches = re.findall(table_pattern, sql_query, re.IGNORECASE)
        
        # Also check for JOIN clauses
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
        join_matches = re.findall(join_pattern, sql_query, re.IGNORECASE)
        
        all_table_refs = table_matches + join_matches
        
        for table_ref in all_table_refs:
            if table_ref not in self.readonly_tables:
                return {
                    "is_valid": False,
                    "error": f"Access to table '{table_ref}' is not allowed"
                }
        
        return {"is_valid": True, "error": None}
    
    def _validate_query_structure(self, sql_query: str) -> Dict:
        """Validate basic SQL query structure"""
        
        query_upper = sql_query.upper()
        
        # Must start with SELECT
        if not query_upper.strip().startswith("SELECT"):
            return {
                "is_valid": False,
                "error": "Query must be a SELECT statement"
            }
        
        # Check for basic SELECT structure
        if "FROM" not in query_upper:
            return {
                "is_valid": False,
                "error": "Query must contain FROM clause"
            }
        
        # Check for balanced parentheses
        if query_upper.count("(") != query_upper.count(")"):
            return {
                "is_valid": False,
                "error": "Unbalanced parentheses in query"
            }
        
        return {"is_valid": True, "error": None}
    
    def _validate_query_limits(self, sql_query: str) -> Dict:
        """Validate query has reasonable limits"""
        
        query_upper = sql_query.upper()
        
        # Check if query has LIMIT clause
        if "LIMIT" not in query_upper:
            return {
                "is_valid": False,
                "error": "Query should include LIMIT clause for large result sets"
            }
        
        # Extract LIMIT value
        limit_pattern = r'LIMIT\s+(\d+)'
        limit_match = re.search(limit_pattern, query_upper)
        
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > settings.MAX_RESULT_ROWS:
                return {
                    "is_valid": False,
                    "error": f"LIMIT value ({limit_value}) exceeds maximum allowed ({settings.MAX_RESULT_ROWS})"
                }
        
        return {"is_valid": True, "error": None}
    
    def sanitize_query(self, sql_query: str) -> str:
        """Sanitize SQL query for safe execution"""
        
        # Remove comments
        sql_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'/\*.*?\*/', '', sql_query, flags=re.DOTALL)
        
        # Remove extra whitespace
        sql_query = re.sub(r'\s+', ' ', sql_query)
        
        # Ensure proper termination
        sql_query = sql_query.strip()
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def extract_table_names(self, sql_query: str) -> List[str]:
        """Extract table names from SQL query"""
        
        table_names = []
        
        # FROM clause
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
        from_matches = re.findall(from_pattern, sql_query, re.IGNORECASE)
        table_names.extend(from_matches)
        
        # JOIN clauses
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
        join_matches = re.findall(join_pattern, sql_query, re.IGNORECASE)
        table_names.extend(join_matches)
        
        return list(set(table_names))  # Remove duplicates
    
    def estimate_query_complexity(self, sql_query: str) -> Dict:
        """Estimate query complexity for monitoring"""
        
        complexity_score = 0
        factors = []
        
        query_upper = sql_query.upper()
        
        # Count tables
        table_count = len(self.extract_table_names(sql_query))
        if table_count > 3:
            complexity_score += 2
            factors.append(f"Multiple table joins ({table_count} tables)")
        
        # Check for subqueries
        if "SELECT" in query_upper and query_upper.count("SELECT") > 1:
            complexity_score += 1
            factors.append("Contains subqueries")
        
        # Check for complex functions
        complex_functions = ["WINDOW", "PARTITION", "OVER", "LAG", "LEAD", "RANK"]
        for func in complex_functions:
            if func in query_upper:
                complexity_score += 1
                factors.append(f"Uses {func} function")
        
        # Check for aggregations
        agg_functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "GROUP BY"]
        agg_count = sum(1 for func in agg_functions if func in query_upper)
        if agg_count > 2:
            complexity_score += 1
            factors.append("Complex aggregations")
        
        return {
            "score": complexity_score,
            "factors": factors,
            "table_count": table_count,
            "is_complex": complexity_score > 3
        } 