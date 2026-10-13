"""HTTP adapter and durable FIFO worker; neither runs a background polling thread."""
import json
import re
from functools import lru_cache
from mangum import Mangum
from .config import load_settings
from .app import create_app,check_runtime
from .db import transaction
from .jobs import work_once

@lru_cache(maxsize=1)
def settings():
    configured=load_settings()
    if configured.worker_enabled or not configured.job_queue_arn:
        raise ValueError("Lambda requires the durable SQS worker")
    check_runtime(configured)
    return configured

@lru_cache(maxsize=1)
def adapter():
    return Mangum(create_app(settings()),lifespan="off")

def web(event,context):
    return adapter()(event,context)

def worker(event,context):
    configured=settings()
    failures=[]
    for record in event["Records"]:
        try:
            if record.get("eventSourceARN")!=configured.job_queue_arn:
                raise ValueError("Unexpected queue")
            message=json.loads(record["body"])
            if set(message)!={"org_id","job_id"} or message["org_id"]!=configured.org_id or not re.fullmatch(r"RUN-[a-f0-9]{32}",message["job_id"]):
                raise ValueError("Invalid work notification")
            work_once(configured,message["job_id"])
            with transaction(configured,configured.org_id) as db:
                job=db.execute("SELECT status FROM jobs WHERE id=%s",(message["job_id"],)).fetchone()
            if not job or job["status"] not in ("completed","failed"):
                raise ValueError("Retry after the durable job commits or its lease expires")
        except Exception:
            failures.append({"itemIdentifier":record["messageId"]})
            break # FIFO ordering: never process later messages after a failure.
    failed_ids={item["itemIdentifier"] for item in failures}
    if failures:
        index=next(i for i,record in enumerate(event["Records"]) if record["messageId"] in failed_ids)
        failures=[{"itemIdentifier":record["messageId"]} for record in event["Records"][index:]]
    return {"batchItemFailures":failures}
