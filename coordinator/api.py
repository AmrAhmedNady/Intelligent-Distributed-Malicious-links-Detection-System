"""
FastAPI Coordinator.
Manages API endpoints, routes scan requests, and handles database operations.
"""
import asyncio
import logging
import sys
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from coordinator.queue_manager import (
    clear_all_results,
    dispatch_to_celery,
    enqueue_job,
    get_job,
    init_db,
    list_all_logs,
    list_queue,
    list_results,
    set_job_status,
    stats_snapshot,
    system_status_snapshot,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NovaShield API",
    description="AI-Based Detection of Malicious Websites",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("NovaShield API started.")


# Data validation models.

class ScanRequest(BaseModel):
    urls: list[str]

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, urls: list[str]) -> list[str]:
        cleaned = []
        for url in urls:
            url = url.strip()
            if not url:
                continue
            if not url.startswith(("http://", "https://")):
                url = "http://" + url
            cleaned.append(url)
        if not cleaned:
            raise ValueError("No valid URLs provided.")
        return cleaned[:20]  # cap at 20 per request


# Health.

@app.get("/health")
def health():
    return {"status": "ok", "service": "NovaShield"}


# System status.

@app.get("/api/system-status")
def get_system_status() -> dict[str, Any]:
    return system_status_snapshot()


# Stats.

@app.get("/api/stats")
def get_stats() -> dict[str, Any]:
    return stats_snapshot()


# Results.

@app.get("/api/results")
def get_results(limit: Annotated[int, Query(ge=1, le=500)] = 100):
    return {"results": list_results(limit)}


@app.delete("/api/results")
def clear_results():
    clear_all_results()
    return {"message": "All scan results cleared."}


# Queue.

@app.get("/api/queue")
def get_queue(limit: Annotated[int, Query(ge=1, le=500)] = 100):
    return {"queue": list_queue(limit)}


# Logs.

@app.get("/api/logs")
def get_logs(limit: Annotated[int, Query(ge=1, le=500)] = 200):
    return {"logs": list_all_logs(limit)}


# Job status.

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# Asynchronous distributed scanning endpoint.

@app.post("/api/scan")
def submit_scan(req: ScanRequest):
    queued = []
    failed = []
    for url in req.urls:
        job_id = enqueue_job(url)
        success = dispatch_to_celery(job_id, url)
        if success:
            queued.append({"job_id": job_id, "url": url})
        else:
            failed.append({"job_id": job_id, "url": url, "error": "Broker unavailable"})
    return {
        "queued": len(queued),
        "failed": len(failed),
        "jobs": queued,
        "failed_jobs": failed,
    }


# Synchronous direct scanning endpoint.

@app.post("/api/scan/direct")
async def direct_scan(req: ScanRequest):
    """
    Scan URLs directly in-process without Redis/Celery.
    Perfect for demo and development use.
    Uses async crawling + feature extraction + ML classification.
    """
    from ml.classifier import get_classifier
    from ml.dataset import MODEL_FEATURE_NAMES
    from ml.feature_extractor import extract, is_trusted
    from ml.nlp_analyzer import analyze
    from ml.risk_rules import apply_risk_rules
    from worker.crawler import fetch_url

    classifier = get_classifier()
    if not classifier.is_ready():
        raise HTTPException(
            status_code=503,
            detail="ML model not trained. Run `python train_model.py` first.",
        )

    async def _scan_one(url: str):
        job_id = enqueue_job(url)
        set_job_status(job_id, "processing")

        try:
            trusted = is_trusted(url)
            if trusted:
                prediction = classifier.predict([], trusted_bypass=True)
                fv_list = [1] * len(MODEL_FEATURE_NAMES)
                nlp_score = 0.0
                keyword_hits = []
            else:
                # Try live crawl (best effort, 8s timeout)
                crawl = await fetch_url(url, timeout=8)
                html = crawl.get("html", "") if crawl else ""

                # Feature extraction
                fv = extract(url, html)
                fv_list = fv.to_list()

                # NLP analysis
                nlp = analyze(html, url)
                nlp_score = nlp.content_score
                keyword_hits = nlp.keyword_hits

                # ML prediction
                prediction = classifier.predict(fv_list)
                prediction = apply_risk_rules(url, prediction, nlp_score=nlp_score, html=html)

            set_job_status(
                job_id, "completed",
                label=prediction.label,
                confidence=prediction.confidence,
                risk_score=prediction.risk_score,
                features=fv_list,
                nlp_score=nlp_score if not trusted else 0.0,
                keyword_hits=keyword_hits if not trusted else [],
                trusted=trusted,
            )
            return {
                "job_id": job_id,
                "url": url,
                "label": prediction.label,
                "confidence": prediction.confidence,
                "risk_score": prediction.risk_score,
                "trusted": trusted,
            }

        except Exception as exc:
            logger.error("Direct scan error for %s: %s", url, exc)
            set_job_status(job_id, "failed", error_msg=str(exc))
            return {"job_id": job_id, "url": url, "error": str(exc)}

    tasks = [_scan_one(url) for url in req.urls]
    results = await asyncio.gather(*tasks)
    return {"results": list(results), "total": len(results)}
