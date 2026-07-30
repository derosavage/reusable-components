import asyncio
import io
import numpy as np
import pandas as pd
from services.analytics_service.analytics import AnalyticsEngine

def _run(coro):
    return asyncio.run(coro)

def test_upload_and_statistics():
    df = pd.DataFrame({"value": np.random.randn(100)})
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    engine = AnalyticsEngine()
    result = _run(engine.upload_csv("test", buf.getvalue()))
    assert "dataset_id" in result
    stats = engine.compute_statistics(result["dataset_id"], "value")
    assert stats["count"] == 100
    engine.close()

def test_correlation():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, 8, 10]})
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    engine = AnalyticsEngine()
    result = _run(engine.upload_csv("corr", buf.getvalue()))
    corr = engine.compute_correlation(result["dataset_id"], "a", "b")
    assert abs(corr - 1.0) < 0.001
    engine.close()
