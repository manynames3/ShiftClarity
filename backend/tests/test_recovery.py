import json
import secrets
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import psycopg
from backend.config import ROOT
from backend.db import transaction
from backend.jobs import work_once,claim,fail
from backend.engine import compute,EngineError
from backend.maintenance import expire_sources,purge_workspace
from .conftest import TEST_ADMIN
from .test_security import upload,decision

def queue(client,bundle):
    batch=upload(client,bundle).json()
    response=client.post("/api/v1/runs",json={"import_id":batch["id"]},headers={"Idempotency-Key":secrets.token_hex(16)})
    assert response.status_code==200,response.text
    return batch,response.json()

def test_backup_restores_sources_rules_run_and_review(environment,clients,bundle):
    client=clients()
    state=client.get("/api/v1/workspace").json()["state"]
    assert client.post("/api/v1/findings/FND-001/decisions",json=decision(state)).status_code==200
    queue(client,bundle)
    assert work_once(environment)
    subprocess.run([sys.executable,str(ROOT/"scripts/recovery-check.py"),"--storage-dir",environment.storage_dir],check=True,capture_output=True)
    result=json.loads((ROOT/"artifacts/pilot-recovery.json").read_text())
    assert result["result"]=="matched"
    assert result["tables"]["completed_runs"]==2 and result["tables"]["write_receipts"]==1
    assert result["private_sources_restored"]>=1

def test_killed_worker_rolls_back_and_replays_once(environment,clients,bundle):
    client=clients()
    batch,job=queue(client,bundle)
    code="""
import json,sys,subprocess,os,signal
from backend.config import Settings,ROOT
from backend import jobs
settings=Settings(**json.load(sys.stdin))
claimed=jobs.claim(settings)
original=jobs.compute
def interrupted(operation,**payload):
    # Stop a real Node parser after launching it, inside the worker's DB transaction.
    child=subprocess.Popen(['node','--max-old-space-size=96',str(ROOT/'backend/engine.mjs')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    os.kill(child.pid,signal.SIGSTOP)
    print(json.dumps({'worker':'computing','parser_pid':child.pid}),flush=True)
    child.communicate(json.dumps({'operation':operation,**payload}))
jobs.compute=interrupted
jobs.execute(settings,claimed)
"""
    worker=subprocess.Popen([sys.executable,"-c",code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,cwd=ROOT)
    worker.stdin.write(json.dumps(environment.__dict__))
    worker.stdin.close()
    started=json.loads(worker.stdout.readline())
    assert started["worker"]=="computing"
    worker.kill()
    worker.wait(timeout=5)
    import os,signal
    os.kill(started["parser_pid"],signal.SIGKILL)
    assert client.get("/api/v1/workspace").json()["state"]["run"]["id"]=="RUN-001"
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE jobs SET lease_until=now()-interval '1 second' WHERE id=%s",(job["id"],))
    assert work_once(environment)
    assert client.get("/api/v1/jobs/"+job["id"]).json()["status"]=="completed"
    with transaction(environment,environment.org_id) as db:
        assert db.execute("SELECT count(*) AS n FROM completed_runs WHERE id=%s",(job["id"],)).fetchone()["n"]==1

def test_retry_limit_and_parser_timeout_preserve_prior_result(environment,clients,bundle):
    client=clients()
    _,job=queue(client,bundle)
    leased=claim(environment)
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE jobs SET attempts=3,lease_until=now()-interval '1 second' WHERE id=%s",(job["id"],))
    assert claim(environment) is None
    state=client.get("/api/v1/workspace").json()["state"]
    assert state["stale"] and state["run"]["id"]=="RUN-001"
    assert client.get("/api/v1/jobs/"+job["id"]).json()["diagnostic"]=="RETRY_LIMIT"
    with patch("backend.engine.subprocess.run",side_effect=subprocess.TimeoutExpired("node",12)):
        import pytest
        with pytest.raises(EngineError,match="PARSER_LIMIT_OR_UNAVAILABLE"):
            compute("validate",text="private-canary")

def test_expired_sources_and_privileged_workspace_purge(environment,clients,bundle):
    client=clients()
    batch=upload(client,bundle).json()
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE imports SET expires_at=now()-interval '1 second'")
    assert client.get("/api/v1/imports/"+batch["id"]+"/source").status_code==404
    assert client.post("/api/v1/runs",json={"import_id":batch["id"]}).status_code==404
    assert expire_sources(environment,TEST_ADMIN)>=1
    with transaction(environment,environment.org_id) as db:
        assert not db.execute("SELECT 1 FROM imports WHERE normalized IS NOT NULL").fetchone()
    import pytest
    with pytest.raises(ValueError):purge_workspace(environment,TEST_ADMIN,"wrong-organization")
    purge_workspace(environment,TEST_ADMIN,environment.org_id)
    assert client.get("/api/v1/workspace").status_code==401
    with psycopg.connect(TEST_ADMIN) as db:
        assert not db.execute("SELECT 1 FROM workspace_heads WHERE org_id=%s",(environment.org_id,)).fetchone()
        assert db.execute("SELECT 1 FROM audit_events WHERE action='workspace_purged'").fetchone()
