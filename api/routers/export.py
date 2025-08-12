"""
Export router for downloading query results
"""

import csv
import json
from io import StringIO
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/csv")
async def export_csv(data: Dict):
    """Export data as CSV"""
    try:
        if not data.get("results") or not data["results"].get("data"):
            raise HTTPException(status_code=400, detail="No data to export")
        
        results = data["results"]
        columns = results.get("columns", [])
        rows = results.get("data", [])
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data rows
        for row in rows:
            writer.writerow([row.get(col, "") for col in columns])
        
        output.seek(0)
        
        # Create streaming response
        def generate():
            yield output.getvalue()
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=bi_export_{data.get('timestamp', 'data')}.csv"
            }
        )
        
    except Exception as e:
        logger.error("CSV export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/json")
async def export_json(data: Dict):
    """Export data as JSON"""
    try:
        if not data.get("results") or not data["results"].get("data"):
            raise HTTPException(status_code=400, detail="No data to export")
        
        # Create JSON response
        export_data = {
            "export_timestamp": data.get("timestamp"),
            "query": data.get("sql_query"),
            "columns": data["results"].get("columns", []),
            "data": data["results"].get("data", []),
            "row_count": data["results"].get("row_count", 0)
        }
        
        return StreamingResponse(
            iter([json.dumps(export_data, indent=2)]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=bi_export_{data.get('timestamp', 'data')}.json"
            }
        )
        
    except Exception as e:
        logger.error("JSON export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/excel")
async def export_excel(data: Dict):
    """Export data as Excel (XLSX)"""
    try:
        if not data.get("results") or not data["results"].get("data"):
            raise HTTPException(status_code=400, detail="No data to export")
        
        # For now, return CSV with Excel headers
        # In production, use a library like openpyxl for proper Excel export
        results = data["results"]
        columns = results.get("columns", [])
        rows = results.get("data", [])
        
        # Create CSV content with Excel-compatible format
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(columns)
        
        # Write data rows
        for row in rows:
            writer.writerow([row.get(col, "") for col in columns])
        
        output.seek(0)
        
        def generate():
            yield output.getvalue()
        
        return StreamingResponse(
            generate(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=bi_export_{data.get('timestamp', 'data')}.xlsx"
            }
        )
        
    except Exception as e:
        logger.error("Excel export failed", error=str(e))
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/formats")
async def get_export_formats():
    """Get available export formats"""
    return {
        "formats": [
            {
                "id": "csv",
                "name": "CSV",
                "description": "Comma-separated values format",
                "media_type": "text/csv"
            },
            {
                "id": "json", 
                "name": "JSON",
                "description": "JavaScript Object Notation format",
                "media_type": "application/json"
            },
            {
                "id": "excel",
                "name": "Excel",
                "description": "Microsoft Excel format (XLSX)",
                "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        ]
    } 