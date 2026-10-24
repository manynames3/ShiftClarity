"""Disposable local integration-test sessions. No production auth bypass or cloud use."""
import json
import secrets
import sys
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import psycopg

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from backend.bootstrap import migrate,seed
from backend.config import load_settings
from backend.engine import digest

settings=load_settings()
if settings.cloud or urlsplit(settings.database_url).hostname not in ['127.0.0.1','localhost']:raise RuntimeError('Local test database required')
parts=urlsplit(settings.database_url)
settings=replace(settings,database_url=urlunsplit(parts._replace(path='/shiftclarity_mvp_browser')),origin='http://127.0.0.1:5196',storage_dir=str(ROOT/'.local/mvp-browser-private'),worker_enabled=True)
admin='postgresql://shiftclarity_local@/postgres?host=/tmp&port=55478'
with psycopg.connect(admin,autocommit=True) as db:
 if not db.execute("SELECT 1 FROM pg_database WHERE datname='shiftclarity_mvp_browser'").fetchone():db.execute('CREATE DATABASE shiftclarity_mvp_browser')
with psycopg.connect(admin.replace('/postgres','/shiftclarity_mvp_browser')) as db:
 migrate(db)
 db.execute('TRUNCATE organizations CASCADE')
 inputs=json.loads((ROOT/'examples/synthetic-healthcare-staffing/bundle.json').read_text())
 draft=json.loads((ROOT/'handoff/data/synthetic/draft_rule.json').read_text())
 seed(db,settings,inputs,draft)
 accounts={}
 for actor,roles in [('MVP-IMPORTER',['owner','importer','reviewer']),('MVP-APPROVER',['approver'])]:
  db.execute('INSERT INTO memberships(issuer,subject,org_id,actor,roles,active) VALUES(%s,%s,%s,%s,%s,true)',(settings.issuer,actor,settings.org_id,actor,roles))
  token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
  db.execute("INSERT INTO sessions VALUES(%s,%s,%s,%s,now()+interval '1 hour')",(digest(token.encode()),settings.issuer,actor,csrf))
  accounts[actor]={'token':token}
for filename,value in [('mvp-browser-config.json',settings.__dict__),('mvp-browser-sessions.json',accounts)]:
 path=ROOT/'.local'/filename;path.write_text(json.dumps(value));path.chmod(0o600)
print('Prepared isolated local browser-test workspace and sessions. No cloud changes.')
