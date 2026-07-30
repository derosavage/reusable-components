from __future__ import annotations
import asyncio
import json
from .celery_app import celery_app


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_daraja_payment(self, phone_number: str, amount: float, account_ref: str):
    try:
        from services.daraja_service.daraja import DarajaClient
        client = DarajaClient()
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(client.stk_push(phone_number, amount, account_ref))
        loop.close()
        return {"status": "completed", "result": result}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def process_analytics_job(self, dataset_id: str, job_type: str, config: str):
    try:
        from services.analytics_service.analytics import AnalyticsEngine
        engine = AnalyticsEngine()
        config_dict = json.loads(config)
        if job_type == "statistics":
            result = engine.compute_statistics(dataset_id, config_dict.get("column", ""))
        elif job_type == "rolling_mean":
            result = engine.compute_rolling_mean(dataset_id, config_dict.get("column", ""), config_dict.get("window", 20))
        elif job_type == "correlation":
            result = engine.compute_correlation(dataset_id, config_dict.get("col1", ""), config_dict.get("col2", ""))
        else:
            result = {"error": f"unknown job type: {job_type}"}
        engine.close()
        return {"status": "completed", "result": result}
    except Exception as exc:
        raise self.retry(exc=exc)
