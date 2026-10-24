"""Prepare an isolated database for browser tests using the real local OIDC provider."""
import json
import sys
from dataclasses import replace
from pathlib import Path
import psycopg
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.config import ROOT,load_settings
from backend.bootstrap import seed,migrate
admin="postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478"
settings=load_settings()
settings=replace(settings,database_url=settings.database_url.rsplit("/",1)[0]+"/shiftclarity_browser_test",storage_dir=str(ROOT/".local/browser-private"))
with psycopg.connect(admin,autocommit=True) as db:
    if not db.execute("SELECT 1 FROM pg_database WHERE datname='shiftclarity_browser_test'").fetchone():
        db.execute("CREATE DATABASE shiftclarity_browser_test")
with psycopg.connect(admin.replace("/postgres","/shiftclarity_browser_test")) as db:
    migrate(db)
    db.execute("TRUNCATE organizations CASCADE")
    inputs=json.loads((ROOT/"artifacts/pilot-template.json").read_text())
    draft=json.loads((ROOT/"handoff/data/synthetic/draft_rule.json").read_text())
    seed(db,settings,inputs,draft)
    db.execute("INSERT INTO organizations VALUES('other-workspace','Isolation test')")
    for account in json.loads((ROOT/".local/accounts.json").read_text()):
        db.execute("INSERT INTO memberships(issuer,subject,org_id,actor,roles,active) VALUES(%s,%s,%s,%s,%s,true)",(settings.issuer,account["id"],account["org"],account["actor"],account["roles"]))
target=ROOT/".local/browser-config.json"
target.write_text(json.dumps(settings.__dict__))
target.chmod(0o600)
print("Isolated synthetic browser-test database prepared.")
