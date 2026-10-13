import copy
import json
import secrets
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import psycopg
import pytest
from backend.app import create_app
from backend.db import transaction
from backend.engine import digest
from backend.jobs import claim,execute,work_once
from backend.storage import PrivateStorage
from .conftest import TEST_ADMIN

def upload(client,bundle):
    return client.post("/api/v1/imports",content=json.dumps(bundle),
        headers={"Content-Type":"application/json","X-Data-Classification":"synthetic","Idempotency-Key":secrets.token_hex(16)})

def decision(state):
    finding=state["run"]["findings"][0]
    return {"action":"confirm","reason":"Checked original rate and approved work","expected_fingerprint":finding["fingerprint"],"expected_version":1,"run_id":state["run"]["id"]}

def test_new_rejected_attempt_blocks_recovered_run_but_exact_retry_does_not(environment,clients,bundle):
    client=clients()
    bad=copy.deepcopy(bundle)
    bad["work"][0]["patient_name"]="SENSITIVE-CANARY"
    def rejected(key):
        return client.post("/api/v1/imports",content=json.dumps(bad),headers={"Content-Type":"application/json","X-Data-Classification":"synthetic","Idempotency-Key":key})
    def recover():
        valid=upload(client,bundle).json()
        assert client.post("/api/v1/runs",json={"import_id":valid["id"]},headers={"Idempotency-Key":secrets.token_hex(16)}).status_code==200
        assert work_once(environment)
        state=client.get("/api/v1/workspace").json()["state"]
        assert not state["stale"]
        return state["run"]
    first_key,second_key=secrets.token_hex(16),secrets.token_hex(16)
    first=rejected(first_key).json()
    assert first["status"]=="failed"
    original=recover()
    assert rejected(first_key).json()["id"]==first["id"]
    assert not client.get("/api/v1/workspace").json()["state"]["stale"]
    assert rejected(second_key).json()["id"]==first["id"]
    state=client.get("/api/v1/workspace").json()["state"]
    assert state["stale"] and state["run"]==original
    assert client.post("/api/v1/findings/FND-001/decisions",json=decision(state)).status_code==409
    recover()
    assert rejected(second_key).json()["id"]==first["id"]
    assert not client.get("/api/v1/workspace").json()["state"]["stale"]
    with transaction(environment,environment.org_id) as db:
        assert db.execute("SELECT count(*) AS n FROM imports WHERE status='failed'").fetchone()["n"]==1

def test_unauthenticated_every_resource(environment):
    client=TestClient(create_app(environment),base_url=environment.origin)
    for path in ["/api/v1/workspace","/api/v1/runs/latest","/api/v1/findings/FND-001","/api/v1/runs/RUN-001/coverage",
                 "/api/v1/documents/DOC-004/access","/api/v1/runs/RUN-001/review-export","/api/v1/audit","/api/v1/members","/api/v1/template","/api/v1/imports"]:
        assert client.get(path).status_code==401,path

def test_identity_roles_csrf_origin_and_revocation(clients):
    reviewer=clients()
    state=reviewer.get("/api/v1/workspace").json()["state"]
    observer=clients("DEMO-OBSERVER")
    assert observer.post("/api/v1/findings/FND-001/decisions",json=decision(state)).status_code==403
    for headers in [{"X-CSRF-Token":"forged"},{"Origin":"https://evil.example"}]:
        assert reviewer.post("/api/v1/findings/FND-001/decisions",json=decision(state),headers=headers).status_code==403
    forged={**decision(state),"actor":"DEMO-APPROVER","tenant_id":"other-workspace"}
    assert reviewer.post("/api/v1/findings/FND-001/decisions",json=forged).status_code==422
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE memberships SET active=false WHERE actor='DEMO-REVIEWER'")
    assert reviewer.get("/api/v1/workspace").status_code==401

def test_cross_organization_guesses_and_rls(environment,clients):
    assert clients("OTHER-REVIEWER").get("/api/v1/workspace").status_code==401
    with transaction(environment,"synthetic-pilot") as db:
        assert len(db.execute("SELECT * FROM workspace_heads").fetchall())==1
        assert not db.execute("SELECT * FROM workspace_heads WHERE org_id='other-workspace'").fetchall()
        with pytest.raises(psycopg.Error):
            db.execute("INSERT INTO completed_runs VALUES('other-workspace','RUN-X','IMP-X','{}',now())")

def test_concurrent_review_conflict_and_receipt(clients):
    one,two=clients(),clients()
    state=one.get("/api/v1/workspace").json()["state"]
    body=decision(state)
    with ThreadPoolExecutor(2) as pool:
        responses=list(pool.map(lambda client:client.post("/api/v1/findings/FND-001/decisions",json=body),[one,two]))
    assert sorted(r.status_code for r in responses)==[200,409]
    winner=one if responses[0].status_code==200 else two
    replay=winner.post("/api/v1/findings/FND-001/decisions",json=body)
    assert replay.status_code==200
    assert replay.json()["state"]["reviews"]
    body["reason"]="Different request reusing same key"
    assert winner.post("/api/v1/findings/FND-001/decisions",json=body).status_code==409
    saved=one.get("/api/v1/workspace").json()["state"]
    review=next(iter(saved["reviews"].values()))
    assert len(review["history"])==1 and review["history"][0]["actor"]=="DEMO-REVIEWER"
    assert review["history"][0]["timestamp"]!=state["run"]["manifest"]["as_of"]

def test_independent_approval_immutable_version(clients,environment):
    author,approver=clients("DEMO-AUTHOR"),clients("DEMO-APPROVER")
    before=approver.get("/api/v1/workspace").json()
    rule_id=before["state"]["draft"]["id"]
    body={"action":"approve","reason":"Amendment inspected","expected_version":before["version"]}
    assert author.post(f"/api/v1/rules/{rule_id}/approval",json=body).status_code==403
    response=approver.post(f"/api/v1/rules/{rule_id}/approval",json=body)
    assert response.status_code==200,response.text
    assert response.json()["state"]["draft"]["approver_id"]=="DEMO-APPROVER"
    assert response.json()["state"]["run"]==before["state"]["run"]
    with transaction(environment,"synthetic-pilot") as db:
        with pytest.raises(psycopg.Error):
            db.execute("UPDATE rule_versions SET content='{}'")

@pytest.mark.parametrize("mutation",["unknown","invalid","real","rule","revision","controls"])
def test_rejected_import_preserves_run_no_raw_diagnostics(mutation,clients,bundle,environment):
    client=clients()
    prior=client.get("/api/v1/workspace").json()["state"]["run"]
    value=copy.deepcopy(bundle)
    if mutation=="unknown":value["work"][0]["patient_name"]="SENSITIVE-CANARY"
    if mutation=="invalid":value["work"][0]["worked_minutes"]=-1
    if mutation=="real":value["manifest"]["synthetic"]=False
    if mutation=="rule":value["rules"][0]["rate"]="999.0000"
    if mutation=="revision":
        assert upload(client,bundle).json()["status"]=="validated"
        value["work"][0]["approval_state"]="pending"
    if mutation=="controls":value["batches"][0]["control_total_minutes"]=0
    response=upload(client,value)
    assert response.status_code==200 and response.json()["status"]=="failed",response.text
    state=client.get("/api/v1/workspace").json()["state"]
    assert state["run"]==prior and state["stale"]
    assert "SENSITIVE-CANARY" not in response.text+json.dumps(state)
    assert list(__import__("pathlib").Path(environment.storage_dir).rglob("*"))
    row=client.get("/api/v1/imports/"+response.json()["id"]).json()
    assert row["diagnostic"] in {"UNSUPPORTED_FIELDS","INVALID_SCHEMA","SYNTHETIC_ONLY","UNAPPROVED_RULE_VERSION","CONFLICTING_SOURCE_REVISION","SOURCE_CONTROLS"}
    assert client.get("/api/v1/imports/"+row["id"]+"/source").status_code==404

def test_content_limits_allowlist_and_opaque_storage(clients,bundle):
    client=clients()
    assert client.post("/api/v1/imports",content="x"*(1024*1024+1)).status_code==413
    assert client.post("/api/v1/imports",content="{}",headers={"Content-Type":"application/zip"}).status_code==415
    response=client.post("/api/v1/imports",content="{malformed",headers={"Content-Type":"application/json","X-Data-Classification":"synthetic"})
    assert response.json()["status"]=="failed"
    result=upload(client,bundle).json()
    source=client.get("/api/v1/imports/"+result["id"]+"/source")
    assert source.status_code==200 and json.loads(source.text)==bundle
    assert clients("DEMO-OBSERVER").get("/api/v1/imports/"+result["id"]+"/source").status_code==403

def test_durable_jobs_retry_atomic_run_and_reopen(environment,clients,bundle):
    client=clients()
    before=client.get("/api/v1/workspace").json()["state"]
    assert client.post("/api/v1/findings/FND-001/decisions",json=decision(before)).status_code==200
    imported=upload(client,bundle).json()
    duplicate=upload(client,bundle).json()
    assert duplicate["id"]==imported["id"]
    key=secrets.token_hex(16)
    first=client.post("/api/v1/runs",json={"import_id":imported["id"]},headers={"Idempotency-Key":key})
    assert client.post("/api/v1/runs",json={"import_id":imported["id"]},headers={"Idempotency-Key":key}).json()["id"]==first.json()["id"]
    leased=claim(environment)
    assert client.get("/api/v1/workspace").json()["state"]["run"]["id"]==before["run"]["id"]
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE jobs SET lease_until=now()-interval '1 second' WHERE id=%s",(leased["id"],))
    replacement=claim(environment)
    execute(environment,leased) # Old lease cannot publish.
    assert client.get("/api/v1/workspace").json()["state"]["run"]["id"]==before["run"]["id"]
    execute(environment,replacement)
    assert client.get("/api/v1/jobs/"+leased["id"]).json()["status"]=="completed"
    published=client.get("/api/v1/workspace").json()["state"]
    assert published["run"]["totals"]==before["run"]["totals"]
    assert next(iter(published["reviews"].values()))["state"]=="confirmed"
    assert not work_once(environment)
    changed=copy.deepcopy(bundle)
    changed["invoices"][0]["amount"]="590.00"
    changed["batches"][1]["signed_control_total"]="6230.00"
    new=upload(client,changed).json()
    queued=client.post("/api/v1/runs",json={"import_id":new["id"]},headers={"Idempotency-Key":secrets.token_hex(16)})
    assert queued.status_code==200,queued.text
    assert work_once(environment)
    reopened=next(iter(client.get("/api/v1/workspace").json()["state"]["reviews"].values()))
    assert reopened["state"]=="needs_review" and len(reopened["history"])==2
    with transaction(environment,"synthetic-pilot") as db:
        assert db.execute("SELECT count(*) AS n FROM completed_runs").fetchone()["n"]==3
        with pytest.raises(psycopg.Error):db.execute("DELETE FROM completed_runs")

def test_append_only_audit_formula_safe_export_and_headers(environment,clients):
    client=clients()
    state=client.get("/api/v1/workspace").json()["state"]
    body={**decision(state),"reason":"=HYPERLINK(\"https://evil.example\")"}
    assert client.post("/api/v1/findings/FND-001/decisions",json=body).status_code==200
    exported=client.get("/api/v1/runs/RUN-001/review-export")
    assert "'=HYPERLINK" in exported.text
    assert "unknown" in exported.text and "no payment evidence" in exported.text
    assert exported.headers["cache-control"]=="no-store" and exported.headers["x-content-type-options"]=="nosniff"
    with transaction(environment,"synthetic-pilot") as db:
        with pytest.raises(psycopg.Error):db.execute("UPDATE audit_events SET actor='forged'")

def test_session_expiry_logout_and_no_public_links(clients,monkeypatch):
    monkeypatch.setattr("backend.auth.logout_url",lambda settings:"https://trusted-provider.example/logout")
    client=clients()
    assert client.get("/api/v1/documents/DOC-004/access").status_code==200
    assert client.get("/api/v1/documents/../../private/access").status_code==404
    expired=clients()
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("UPDATE sessions SET expires_at=now()-interval '1 second' WHERE digest=%s",(digest(expired.cookies.get("sc_session").encode()),))
    assert expired.get("/api/v1/workspace").status_code==401
    assert client.post("/auth/logout",json={}).status_code==200
    assert client.get("/api/v1/workspace").status_code==401

def test_source_registration_new_draft_and_successive_approval(clients):
    author=clients("DEMO-AUTHOR")
    approver=clients("DEMO-APPROVER")
    observer=clients("DEMO-OBSERVER")
    source={"title":"Fictional October amendment","text":"Standard RN rate USD 70.00 effective October 20, 2026. Supersedes the October 13 amendment.","synthetic":True}
    assert observer.post("/api/v1/documents",json=source).status_code==403
    result=author.post("/api/v1/documents",json=source)
    assert result.status_code==200,result.text
    assert author.post("/api/v1/documents",json=source).json()==result.json()
    excerpt=result.json()["state"]["inputs"]["excerpts"][-1]
    current=approver.get("/api/v1/workspace").json()
    approved=approver.post("/api/v1/rules/"+current["state"]["draft"]["id"]+"/approval",
        json={"action":"approve","reason":"Initial amendment checked","expected_version":current["version"]})
    assert approved.status_code==200,approved.text
    prior=approved.json()["state"]["draft"]["id"]
    author.headers["Idempotency-Key"]=secrets.token_hex(16)
    draft=author.post("/api/v1/rules/drafts",json={"supersedes":prior,"source_excerpt_id":excerpt["id"],
        "rate":"70","effective_from":"2026-10-20","expected_version":approved.json()["version"]})
    assert draft.status_code==200,draft.text
    assert draft.json()["state"]["draft"]["author_id"]=="DEMO-AUTHOR"
    approver.headers["Idempotency-Key"]=secrets.token_hex(16)
    second=approver.post("/api/v1/rules/"+draft.json()["state"]["draft"]["id"]+"/approval",
        json={"action":"approve","reason":"Source and effective date inspected","expected_version":draft.json()["version"]})
    assert second.status_code==200,second.text
    assert second.json()["state"]["draft"]["rate"]=="70.0000"
    assert second.json()["state"]["run"]==current["state"]["run"]

def test_catalog_and_draft_authority_survive_empty_snapshot(environment,clients,bundle):
    client=clients()
    value=copy.deepcopy(bundle)
    for key in ["work","invoices","rules","batches","excerpts"]:
        value[key]=[]
    value["manifest"]["invoice_coverage_complete"]=False
    imported=upload(client,value).json()
    assert imported["status"]=="validated"
    assert client.post("/api/v1/runs",json={"import_id":imported["id"]}).status_code==200
    assert work_once(environment)
    current=clients("DEMO-APPROVER").get("/api/v1/workspace").json()
    assert current["state"]["run"]["coverage"]["received_records"]==0
    assert len(current["catalog"]["rules"])==3 and len(current["catalog"]["excerpts"])==4
    approver=clients("DEMO-APPROVER")
    result=approver.post("/api/v1/rules/"+current["state"]["draft"]["id"]+"/approval",
        json={"action":"approve","reason":"Original registered source reviewed","expected_version":current["version"]})
    assert result.status_code==200,result.text
    assert result.json()["state"]["inputs"]["rules"]==[]
    assert result.json()["state"]["run"]==current["state"]["run"]

def test_accepted_import_cannot_be_rewritten(environment,clients,bundle):
    client=clients()
    upload(client,bundle)
    with transaction(environment,environment.org_id) as db:
        with pytest.raises(psycopg.Error):
            db.execute("UPDATE imports SET normalized='{}' WHERE status='validated'")

def test_interrupted_quarantine_and_parallel_retry_are_safe(environment,clients,bundle):
    client=clients()
    value=copy.deepcopy(bundle)
    value["manifest"]["note"]="Synthetic quarantine recovery test"
    data=json.dumps(value).encode()
    key=environment.org_id+"/quarantine/"+"c"*32
    storage=PrivateStorage(environment)
    storage.put(key,data)
    storage.put(key.replace("/quarantine/","/accepted/"),data)
    identifier="IMP-QUARANTINE-RECOVERY"
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("INSERT INTO imports(id,org_id,request_key,content_hash,object_key,status) VALUES(%s,%s,%s,%s,%s,'quarantined')",
                   (identifier,environment.org_id,secrets.token_hex(16),digest(data),key))
    other=clients()
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda actor:upload(actor,value),[client,other]))
    assert all(r.status_code==200 and r.json()["status"]=="validated" for r in results)
    assert all(r.json()["id"]==identifier for r in results)
    assert all("object_key" not in r.json() for r in results)
    assert client.get("/api/v1/imports/"+identifier+"/source").content==data
    with transaction(environment,environment.org_id) as db:
        assert db.execute("SELECT count(*) AS n FROM audit_events WHERE action='import_validated' AND resource=%s",(identifier,)).fetchone()["n"]==1
