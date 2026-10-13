import json
import secrets
from dataclasses import replace
from unittest.mock import patch
import pytest
import psycopg
from backend.lambda_handler import worker,web,adapter
from backend.jobs import notify
from .conftest import TEST_ADMIN
from .test_security import upload
from backend.config import ROOT

QUEUE="arn:aws:sqs:us-east-1:636305658578:shiftclarity-synthetic-jobs.fifo"

def test_only_public_build_assets_are_cached(environment,clients):
    client=clients()
    asset=next((ROOT/"dist/assets").glob("index-*.js"))
    response=client.get("/assets/"+asset.name)
    assert response.status_code==200
    assert response.headers["cache-control"]=="public, max-age=31536000, immutable"
    for path in ("/api/v1/session","/api/v1/workspace","/api/v1/imports","/pilot/"):
        assert client.get(path).headers["cache-control"]=="no-store"

def message(job_id,org="synthetic-pilot",queue=QUEUE):
    return {"Records":[{"messageId":"notice-1","eventSourceARN":queue,
                         "body":json.dumps({"org_id":org,"job_id":job_id})}]}

def test_fifo_notification_failure_rolls_back_job(environment,clients,bundle):
    client=clients()
    batch=upload(client,bundle).json()
    with patch("backend.app.jobs.notify",side_effect=RuntimeError("queue unavailable")):
        response=client.post("/api/v1/runs",json={"import_id":batch["id"]})
    assert response.status_code==503
    with psycopg.connect(TEST_ADMIN) as db:
        assert db.execute("SELECT count(*) FROM jobs").fetchone()[0]==0
        assert db.execute("SELECT id FROM completed_runs").fetchall()==[("RUN-001",)]

def test_fifo_worker_targets_one_job_and_replays_once(environment,clients,bundle):
    client=clients()
    batch=upload(client,bundle).json()
    job_ids=[]
    for _ in range(2):
        result=client.post("/api/v1/runs",json={"import_id":batch["id"]},headers={"Idempotency-Key":secrets.token_hex(16)})
        assert result.status_code==200
        job_ids.append(result.json()["id"])
    configured=replace(environment,job_queue_arn=QUEUE)
    with patch("backend.lambda_handler.settings",return_value=configured):
        assert worker(message(job_ids[1]),None)=={"batchItemFailures":[]}
        assert worker(message(job_ids[1]),None)=={"batchItemFailures":[]}
    assert client.get("/api/v1/jobs/"+job_ids[0]).json()["status"]=="queued"
    assert client.get("/api/v1/jobs/"+job_ids[1]).json()["status"]=="completed"
    with psycopg.connect(TEST_ADMIN) as db:
        assert db.execute("SELECT count(*) FROM completed_runs WHERE id=%s",(job_ids[1],)).fetchone()[0]==1

@pytest.mark.parametrize("org,queue",[("other-workspace",QUEUE),("synthetic-pilot","other-queue")])
def test_worker_rejects_cross_workspace_or_queue(environment,org,queue):
    configured=replace(environment,job_queue_arn=QUEUE)
    with patch("backend.lambda_handler.settings",return_value=configured),patch("backend.lambda_handler.work_once") as execute:
        assert worker(message("RUN-"+"a"*32,org,queue),None)=={"batchItemFailures":[{"itemIdentifier":"notice-1"}]}
        execute.assert_not_called()

def test_notification_may_precede_database_commit_and_retry(environment):
    configured=replace(environment,job_queue_arn=QUEUE)
    with patch("backend.lambda_handler.settings",return_value=configured):
        assert worker(message("RUN-"+"b"*32),None)=={"batchItemFailures":[{"itemIdentifier":"notice-1"}]}

def test_notice_contains_identity_not_financial_data(environment):
    configured=replace(environment,job_queue_url="https://sqs.us-east-1.amazonaws.com/636305658578/shiftclarity-synthetic-jobs.fifo")
    with patch("backend.jobs.boto3.client") as sqs:
        notify(configured,"RUN-"+"c"*32)
        args=sqs.return_value.send_message.call_args.kwargs
        assert json.loads(args["MessageBody"])=={"org_id":environment.org_id,"job_id":"RUN-"+"c"*32}
        assert args["MessageGroupId"]==environment.org_id
        assert args["MessageDeduplicationId"]=="RUN-"+"c"*32

@pytest.mark.parametrize("path,status",[("/health",200),("/api/v1/workspace",401)])
def test_actual_mangum_http_api_adapter(environment,path,status):
    host=environment.origin.split("://",1)[1]
    event={"version":"2.0","routeKey":"$default","rawPath":path,"rawQueryString":"","headers":{"host":host},
           "requestContext":{"http":{"method":"GET","path":path,"sourceIp":"127.0.0.1","protocol":"HTTP/1.1"},
                             "domainName":host,"stage":"$default"},"isBase64Encoded":False}
    adapter.cache_clear()
    try:
        with patch("backend.lambda_handler.settings",return_value=environment):
            result=web(event,None)
        assert result["statusCode"]==status
        assert "frame-ancestors 'none'" in result["headers"]["content-security-policy"]
    finally:
        adapter.cache_clear()
