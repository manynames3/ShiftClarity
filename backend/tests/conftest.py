import json
import secrets
from dataclasses import replace
from pathlib import Path
import pytest
import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from fastapi.testclient import TestClient
from backend.config import load_settings, ROOT
from backend.engine import compute,digest
from backend.app import create_app
from backend.bootstrap import seed,migrate

ADMIN="postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478"
TEST_ADMIN=ADMIN.replace("/postgres","/shiftclarity_test")

@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    local=load_settings()
    from urllib.parse import urlsplit
    if local.cloud or urlsplit(local.database_url).hostname not in ['127.0.0.1','localhost']:raise RuntimeError('Tests require the dedicated local configuration; cloud targets are refused.')
    with psycopg.connect(ADMIN,autocommit=True) as db:
        if not db.execute("SELECT 1 FROM pg_database WHERE datname='shiftclarity_test'").fetchone():
            db.execute("CREATE DATABASE shiftclarity_test")
    with psycopg.connect(TEST_ADMIN) as db:
        migrate(db)
        db.execute("GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO shiftclarity_app")
        db.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO shiftclarity_app")
        db.execute("REVOKE UPDATE,DELETE ON audit_events,completed_runs,rule_versions,source_revisions FROM shiftclarity_app")
    return replace(local,database_url=local.database_url.rsplit("/",1)[0]+"/shiftclarity_test",
                   storage_dir=str(tmp_path_factory.mktemp("private")),worker_enabled=False)

@pytest.fixture
def bundle():
    return json.loads((ROOT/"artifacts/pilot-template.json").read_text())

@pytest.fixture
def environment(settings,bundle):
    with psycopg.connect(TEST_ADMIN) as db:
        db.execute("TRUNCATE organizations CASCADE")
        db.execute("TRUNCATE auth_flows")
        db.execute("INSERT INTO organizations VALUES('synthetic-pilot','Test'),('other-workspace','Other')")
        draft=json.loads((ROOT/"handoff/data/synthetic/draft_rule.json").read_text())
        seed(db,settings,bundle,draft)
        state=compute("seed",inputs=bundle,draft=draft)
        db.execute("INSERT INTO workspace_heads(org_id,state) VALUES('other-workspace',%s)",(Jsonb(state),))
        for actor,roles,org in [("DEMO-REVIEWER",["reviewer","importer"],"synthetic-pilot"),
                               ("DEMO-AUTHOR",["author","approver"],"synthetic-pilot"),
                               ("DEMO-APPROVER",["approver"],"synthetic-pilot"),
                               ("DEMO-OBSERVER",[],"synthetic-pilot"),("OTHER-REVIEWER",["reviewer"],"other-workspace")]:
            db.execute("INSERT INTO memberships(issuer,subject,org_id,actor,roles,active) VALUES(%s,%s,%s,%s,%s,true)",(settings.issuer,actor,org,actor,roles))
    return settings

@pytest.fixture
def clients(environment):
    created=[]
    def make(actor="DEMO-REVIEWER"):
        token=secrets.token_urlsafe(32)
        csrf=secrets.token_urlsafe(32)
        with psycopg.connect(TEST_ADMIN) as db:
            db.execute("INSERT INTO sessions VALUES(%s,%s,%s,%s,now()+interval '15 minutes')",
                       (digest(token.encode()),environment.issuer,actor,csrf))
        client=TestClient(create_app(environment),base_url=environment.origin,raise_server_exceptions=False)
        client.cookies.set("sc_session",token)
        client.headers.update({"Origin":environment.origin,"X-CSRF-Token":csrf,"Idempotency-Key":secrets.token_hex(16)})
        created.append(client)
        return client
    yield make
    for client in created:
        client.close()
