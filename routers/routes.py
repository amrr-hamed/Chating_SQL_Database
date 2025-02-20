from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Dict, Any
from services.db_manager import DatabaseManager
from services.schema_retriever import SchemaRetriever
from services.pipeline import TextToSQLPipeline
from services.query_executor import QueryExecutionError

router = APIRouter()
db_manager = DatabaseManager()
schema_retriever = SchemaRetriever()
pipeline = TextToSQLPipeline()

@router.post("/upload", tags=["database"])
async def upload_database(
    file: UploadFile, 
    background_tasks: BackgroundTasks
):
    """Handle database uploads and schema indexing"""
    try:
        db_path = await db_manager.save_database(file)
        print(f"Saved database to: {db_path.absolute()}")  # Debug line
        background_tasks.add_task(process_upload_background, db_path)
        return JSONResponse(
            content={"message": "Upload processing started", "db_id": str(db_path.name)},
            status_code=202
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def process_upload_background(db_path: Path):
    """Background task for schema processing"""
    try:
        schema_data = db_manager.extract_schema(db_path)
        schema_retriever.update_index(schema_data, db_path.name)
    except Exception as e:
        # Implement proper error logging here
        print(f"Background processing failed for {db_path}: {str(e)}")

@router.post("/chat", tags=["query"])
async def chat_with_database(query: dict) -> Dict[str, Any]:
    """
    Handle natural language queries
    Expects JSON: {"question": "your question", "db_id": "uploaded_db_id"}
    """
    try:
        if not query.get("question"):
            raise ValueError("Missing 'question' in request body")
            
        db_id = query.get("db_id")
        if not db_id:
            raise ValueError("Missing 'db_id' in request body")
            
        db_path = db_manager.get_db_path(db_id)
        if not db_path.exists():
            raise FileNotFoundError(f"Database {db_id} not found")

        results, error = pipeline.process_query(query["question"], db_path)
        
        if error:
            return JSONResponse(
                content={"error": error},
                status_code=400
            )
            
        return {"results": results, "error": None}
        
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except QueryExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")