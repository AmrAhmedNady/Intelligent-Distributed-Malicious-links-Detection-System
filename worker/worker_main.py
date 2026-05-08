"""
Celery Worker.
Pulls tasks from Redis, executes web crawls, and runs ML classification.
"""
import asyncio
import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "novashield",
    broker=REDIS_URL,
    backend=REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)


@celery_app.task(bind=True, name="novashield.scan_url", max_retries=2)
def scan_url_task(self, job_id: str, url: str):
    """Celery task: crawl + classify a URL and store result."""
    from coordinator.queue_manager import set_job_status
    from ml.classifier import get_classifier
    from ml.dataset import MODEL_FEATURE_NAMES
    from ml.feature_extractor import extract, is_trusted
    from ml.nlp_analyzer import analyze
    from ml.risk_rules import apply_risk_rules
    from worker.crawler import fetch_url

    logger.info("[%s] Starting scan: %s", job_id, url)
    set_job_status(job_id, "processing")

    try:
        trusted = is_trusted(url)
        classifier = get_classifier()

        if trusted:
            prediction = classifier.predict([], trusted_bypass=True)
            fv_list = [1] * len(MODEL_FEATURE_NAMES)
            nlp_score = 0.0
            keyword_hits = []
        else:
            # Run async crawl in sync context
            loop = asyncio.new_event_loop()
            try:
                crawl = loop.run_until_complete(fetch_url(url, timeout=15))
            finally:
                loop.close()

            html = crawl.get("html", "") if crawl else ""
            fv = extract(url, html)
            fv_list = fv.to_list()

            nlp = analyze(html, url)
            nlp_score = nlp.content_score
            keyword_hits = nlp.keyword_hits

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
        logger.info("[%s] Done: %s → %s (%.1f%%)", job_id, url, prediction.label, prediction.confidence * 100)

    except Exception as exc:
        logger.error("[%s] Error: %s", job_id, exc)
        try:
            raise self.retry(exc=exc, countdown=5)
        except Exception:
            set_job_status(job_id, "failed", error_msg=str(exc))
