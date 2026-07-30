from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from shared.config import settings
from .analytics import AnalyticsEngine

router = APIRouter()
engine = AnalyticsEngine()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), name: Optional[str] = Form(None)):
    content = await file.read()
    if len(content) > settings.ANALYTICS_MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds maximum size")
    dataset_name = name or file.filename or "unnamed"
    if file.filename and file.filename.endswith(".parquet"):
        result = await engine.upload_parquet(dataset_name, content)
    else:
        result = await engine.upload_csv(dataset_name, content)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result

@router.get("/datasets")
def list_datasets():
    return {"datasets": engine.list_datasets()}

@router.get("/statistics/{dataset_id}")
def get_statistics(dataset_id: str, column: str = Query(...)):
    stats = engine.compute_statistics(dataset_id, column)
    if "error" in stats:
        raise HTTPException(404, stats["error"])
    return stats

@router.get("/rolling/{dataset_id}")
def get_rolling_mean(dataset_id: str, column: str = Query(...), window: int = Query(20, ge=2)):
    result = engine.compute_rolling_mean(dataset_id, column, window)
    if not result:
        raise HTTPException(404, "Dataset or column not found")
    return {"column": column, "window": window, "values": result}

@router.get("/correlation/{dataset_id}")
def get_correlation(dataset_id: str, col1: str = Query(...), col2: str = Query(...)):
    return {"col1": col1, "col2": col2, "correlation": engine.compute_correlation(dataset_id, col1, col2)}

@router.post("/sql")
def run_sql(query: str = Query(...)):
    try:
        return {"results": engine.sql_query(query)}
    except Exception as e:
        raise HTTPException(400, f"SQL error: {str(e)}")

@router.get("/health")
def health():
    return {"status": "ok", "service": "analytics"}
