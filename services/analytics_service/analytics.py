from __future__ import annotations

import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import duckdb
import numpy as np
import pandas as pd

from shared.config import settings


class AnalyticsEngine:
    def __init__(self):
        os.makedirs(settings.ANALYTICS_UPLOAD_DIR, exist_ok=True)
        self.duck = duckdb.connect(settings.DUCKDB_PATH)
        self._init_db()

    def _init_db(self):
        self.duck.execute("CREATE TABLE IF NOT EXISTS datasets (id VARCHAR PRIMARY KEY, name VARCHAR, uploaded_at TIMESTAMP, row_count INTEGER, columns VARCHAR, file_path VARCHAR)")
        self.duck.execute("CREATE TABLE IF NOT EXISTS metrics (id VARCHAR PRIMARY KEY, dataset_id VARCHAR, metric_name VARCHAR, value DOUBLE, computed_at TIMESTAMP, config VARCHAR)")

    async def upload_csv(self, name: str, content: bytes) -> Dict[str, Any]:
        dataset_id = str(uuid.uuid4())
        file_path = os.path.join(settings.ANALYTICS_UPLOAD_DIR, f"{dataset_id}.csv")
        with open(file_path, "wb") as f:
            f.write(content)
        df = pd.read_csv(file_path)
        if df.empty:
            os.remove(file_path)
            return {"error": "empty dataset"}
        parquet_path = file_path.replace(".csv", ".parquet")
        df.to_parquet(parquet_path, index=False)
        self.duck.execute("INSERT INTO datasets VALUES (?, ?, ?, ?, ?, ?)", [dataset_id, name, datetime.now(timezone.utc), len(df), str(list(df.columns)), parquet_path])
        os.remove(file_path)
        return {"dataset_id": dataset_id, "name": name, "row_count": len(df), "columns": list(df.columns)}

    async def upload_parquet(self, name: str, content: bytes) -> Dict[str, Any]:
        dataset_id = str(uuid.uuid4())
        file_path = os.path.join(settings.ANALYTICS_UPLOAD_DIR, f"{dataset_id}.parquet")
        with open(file_path, "wb") as f:
            f.write(content)
        df = pd.read_parquet(file_path)
        if df.empty:
            os.remove(file_path)
            return {"error": "empty dataset"}
        self.duck.execute("INSERT INTO datasets VALUES (?, ?, ?, ?, ?, ?)", [dataset_id, name, datetime.now(timezone.utc), len(df), str(list(df.columns)), file_path])
        return {"dataset_id": dataset_id, "name": name, "row_count": len(df), "columns": list(df.columns)}

    def get_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        result = self.duck.execute("SELECT file_path FROM datasets WHERE id = ?", [dataset_id]).fetchone()
        if not result:
            return None
        return pd.read_parquet(result[0])

    def compute_statistics(self, dataset_id: str, column: str) -> Dict[str, Any]:
        df = self.get_dataset(dataset_id)
        if df is None:
            return {"error": "dataset not found"}
        if column not in df.columns:
            return {"error": f"column '{column}' not found"}
        arr = df[column].dropna().to_numpy(dtype=np.float64)
        if len(arr) == 0:
            return {"error": "column has no numeric data"}
        stats = {
            "count": len(arr),
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
            "q1": float(np.percentile(arr, 25)),
            "q3": float(np.percentile(arr, 75)),
            "skewness": float(pd.Series(arr).skew()),
            "kurtosis": float(pd.Series(arr).kurtosis()),
        }
        metric_id = str(uuid.uuid4())
        self.duck.execute("INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?)", [metric_id, dataset_id, f"statistics_{column}", 0.0, datetime.now(timezone.utc), str(stats)])
        return stats

    def compute_rolling_mean(self, dataset_id: str, column: str, window: int = 20) -> List[float]:
        df = self.get_dataset(dataset_id)
        if df is None or column not in df.columns:
            return []
        arr = df[column].dropna().to_numpy(dtype=np.float64)
        rolling_window = deque(maxlen=window)
        result = []
        for val in arr:
            rolling_window.append(val)
            result.append(float(np.mean(rolling_window)))
        return result

    def compute_correlation(self, dataset_id: str, col1: str, col2: str) -> float:
        df = self.get_dataset(dataset_id)
        if df is None:
            return 0.0
        arr1 = df[col1].to_numpy(dtype=np.float64)
        arr2 = df[col2].to_numpy(dtype=np.float64)
        return float(np.corrcoef(arr1, arr2)[0, 1])

    def list_datasets(self) -> List[Dict[str, Any]]:
        rows = self.duck.execute("SELECT id, name, uploaded_at, row_count, columns FROM datasets ORDER BY uploaded_at DESC").fetchall()
        return [{"id": r[0], "name": r[1], "uploaded_at": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]), "row_count": r[3], "columns": eval(r[4]) if isinstance(r[4], str) else r[4]} for r in rows]

    def sql_query(self, query: str) -> List[Dict[str, Any]]:
        results = self.duck.execute(query).fetchdf()
        return results.to_dict(orient="records")

    def close(self):
        self.duck.close()