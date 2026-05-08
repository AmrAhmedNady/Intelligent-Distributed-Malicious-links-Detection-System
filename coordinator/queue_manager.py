"""
Queue and Database Manager.
Provides an SQLite-backed interface for tracking job states and logs.
"""
import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "novashield.db"


@contextmanager
def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id      TEXT PRIMARY KEY,
                url         TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'queued',
                label       TEXT,
                confidence  REAL,
                risk_score  REAL,
                features    TEXT,
                nlp_score   REAL,
                keyword_hits TEXT,
                error_msg   TEXT,
                trusted     INTEGER DEFAULT 0,
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL
            )
        """)
    logger.info("Database initialized at %s", DB_PATH)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for key in ("features", "keyword_hits"):
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except Exception:
                pass
    return d


def enqueue_job(url: str) -> str:
    """Create a new job record and return its job_id."""
    import time
    job_id = str(uuid.uuid4())
    now = time.time()
    with _db() as conn:
        conn.execute(
            "INSERT INTO jobs (job_id, url, status, created_at, updated_at) VALUES (?,?,?,?,?)",
            (job_id, url, "queued", now, now),
        )
    return job_id


def dispatch_to_celery(job_id: str, url: str) -> bool:
    """Try to dispatch job to Celery worker. Returns True if successful."""
    try:
        from worker.worker_main import scan_url_task
        scan_url_task.apply_async(args=[job_id, url], task_id=job_id)
        set_job_status(job_id, "queued")
        return True
    except Exception as exc:
        logger.warning("Celery dispatch failed for %s: %s", job_id, exc)
        set_job_status(job_id, "failed", error_msg=f"Broker unavailable: {exc}")
        return False


def set_job_status(
    job_id: str,
    status: str,
    *,
    label: Optional[str] = None,
    confidence: Optional[float] = None,
    risk_score: Optional[float] = None,
    features: Optional[list] = None,
    nlp_score: Optional[float] = None,
    keyword_hits: Optional[list] = None,
    error_msg: Optional[str] = None,
    trusted: bool = False,
):
    import time
    with _db() as conn:
        conn.execute(
            """UPDATE jobs SET
                status=?, label=?, confidence=?, risk_score=?,
                features=?, nlp_score=?, keyword_hits=?,
                error_msg=?, trusted=?, updated_at=?
               WHERE job_id=?""",
            (
                status, label, confidence, risk_score,
                json.dumps(features) if features else None,
                nlp_score,
                json.dumps(keyword_hits) if keyword_hits else None,
                error_msg, int(trusted), time.time(),
                job_id,
            ),
        )


def get_job(job_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_results(limit: int = 100) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status='completed' ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def list_queue(limit: int = 100) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE status IN ('queued','processing') ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def list_all_logs(limit: int = 200) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def stats_snapshot() -> dict[str, Any]:
    with _db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs WHERE status='completed'").fetchone()[0]
        malicious = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='completed' AND label='malicious'"
        ).fetchone()[0]
        benign = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='completed' AND label='benign'"
        ).fetchone()[0]
        avg_conf = conn.execute(
            "SELECT AVG(confidence) FROM jobs WHERE status='completed'"
        ).fetchone()[0] or 0.0
        queued = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('queued','processing')"
        ).fetchone()[0]
        failed = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='failed'"
        ).fetchone()[0]

    return {
        "total_scanned": total,
        "malicious": malicious,
        "benign": benign,
        "queued": queued,
        "failed": failed,
        "avg_confidence": round(avg_conf, 4),
        "malicious_pct": round(malicious / total * 100, 1) if total else 0.0,
    }


def clear_all_results():
    with _db() as conn:
        conn.execute("DELETE FROM jobs WHERE status='completed'")


def system_status_snapshot() -> dict:
    """Check if Redis broker and Celery workers are reachable."""
    broker_online = False
    worker_online = False
    try:
        import os
        import redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=1)
        r.ping()
        broker_online = True
    except Exception:
        pass

    try:
        from worker.worker_main import celery_app
        inspect = celery_app.control.inspect(timeout=1)
        active = inspect.active()
        worker_online = bool(active)
    except Exception:
        pass

    return {
        "broker_online": broker_online,
        "worker_online": worker_online,
        "status": "ok" if (broker_online and worker_online) else "degraded",
    }
