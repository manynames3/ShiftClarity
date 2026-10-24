import uuid
import threading
import json
import boto3
from datetime import datetime, timezone
from psycopg.types.json import Jsonb
from .db import transaction, audit, head, save_head,store_review
from .engine import compute, EngineError

def notify(settings,job_id):
    if settings.job_queue_url:
        boto3.client("sqs",region_name=settings.region).send_message(
            QueueUrl=settings.job_queue_url,MessageGroupId=settings.org_id,MessageDeduplicationId=job_id,
            MessageBody=json.dumps({"org_id":settings.org_id,"job_id":job_id}))

def claim(settings,job_id=None):
    lease=uuid.uuid4().hex
    with transaction(settings,settings.org_id) as db:
        exhausted=db.execute("UPDATE jobs SET status='failed',diagnostic='RETRY_LIMIT',lease_until=NULL WHERE status='reconciling' AND lease_until<now() AND attempts>=3 RETURNING id,actor").fetchall()
        if exhausted:
            state=head(db,True)["state"]
            state.update(stale=True,error="Worker retry limit reached; previous result retained.",importState="failed")
            save_head(db,settings.org_id,state)
            for failed in exhausted:
                audit(db,settings.org_id,failed["actor"],"run_failed",failed["id"],{"code":"RETRY_LIMIT"})
        job=db.execute("""
          SELECT * FROM jobs WHERE attempts<3 AND
          ((status='queued' AND available_at<=now()) OR (status='reconciling' AND lease_until<now()))
          AND (%s::text IS NULL OR id=%s)
          ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1
        """,(job_id,job_id)).fetchone()
        if not job:
            return None
        db.execute("UPDATE jobs SET status='reconciling',attempts=attempts+1,lease_until=now()+interval '60 seconds',lease_token=%s WHERE id=%s",
                   (lease,job["id"]))
        job["lease_token"]=lease
        return job

def execute(settings,job):
    # Serialize publication and review writes, and fence workers whose lease was reclaimed.
    with transaction(settings,settings.org_id) as db:
        current=db.execute("SELECT * FROM jobs WHERE id=%s FOR UPDATE",(job["id"],)).fetchone()
        if current["status"]!="reconciling" or current["lease_token"]!=job["lease_token"]:
            return
        snapshot=head(db,True)["state"]
        store_review(db,settings.org_id,snapshot)
        batch=db.execute("SELECT normalized FROM imports WHERE id=%s AND status='validated'",(job["import_id"],)).fetchone()
        if not batch:
            raise EngineError("SOURCE_UNAVAILABLE")
        inputs=batch["normalized"]
        previous=db.execute("SELECT state FROM review_workspaces WHERE state#>>'{run,manifest,dataset_id}'=%s ORDER BY created_at DESC,run_id DESC LIMIT 1",(inputs['manifest']['dataset_id'],)).fetchone()
        snapshot['reviews']=previous['state'].get('reviews',{}) if previous else {}
        snapshot['localTasks']=previous['state'].get('localTasks',[]) if previous else []
        if previous:snapshot['run']=previous['state']['run']
        inputs["manifest"]["run_id"]=job["id"]
        published=compute("publish",state=snapshot,inputs=inputs,timestamp=datetime.now(timezone.utc).isoformat())
        db.execute("INSERT INTO completed_runs(org_id,id,import_id,snapshot) VALUES(%s,%s,%s,%s)",
                   (settings.org_id,job["id"],job["import_id"],Jsonb(published)))
        save_head(db,settings.org_id,published)
        from .workflow import sync_cases
        sync_cases(db,settings.org_id,published)
        db.execute("UPDATE jobs SET status='completed',lease_until=NULL WHERE id=%s",(job["id"],))
        audit(db,settings.org_id,job["actor"],"run_published",job["id"])

def fail(settings,job,code):
    with transaction(settings,settings.org_id) as db:
        current=db.execute("SELECT * FROM jobs WHERE id=%s FOR UPDATE",(job["id"],)).fetchone()
        if current["status"]!="reconciling" or current["lease_token"]!=job["lease_token"]:
            return
        terminal=current["attempts"]>=3 or code=="VALIDATION_OR_CONFLICT"
        db.execute("UPDATE jobs SET status=%s,diagnostic=%s,available_at=now()+interval '5 seconds',lease_until=NULL WHERE id=%s",
                   ("failed" if terminal else "queued",code,job["id"]))
        if terminal:
            state=head(db,True)["state"]
            state.update(stale=True,error="Run failed validation; previous completed result retained.",importState="failed")
            save_head(db,settings.org_id,state)
        audit(db,settings.org_id,job["actor"],"run_failed" if terminal else "run_retry",job["id"],{"code":code})

def work_once(settings,job_id=None):
    job=claim(settings,job_id)
    if not job:
        return False
    try:
        execute(settings,job)
    except EngineError as error:
        fail(settings,job,str(error))
    except Exception:
        fail(settings,job,"WORKER_UNAVAILABLE")
    return True

def loop(settings,stop,wake=None):
    wake=wake or threading.Event()
    wake.set()
    while not stop.is_set():
        wake.wait()
        wake.clear()
        if stop.is_set():
            break
        try:
            while not stop.is_set() and work_once(settings):
                pass
            with transaction(settings,settings.org_id) as db:
                pending=db.execute("SELECT count(*) AS n FROM jobs WHERE status IN ('queued','reconciling')").fetchone()["n"]
        except Exception:
            pending=1
        # Idle workspaces do not poll Postgres, allowing Neon compute to suspend.
        if pending:
            wake.wait(5)
            if not stop.is_set():
                wake.set()

