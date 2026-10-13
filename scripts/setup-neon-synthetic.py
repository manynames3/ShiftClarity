"""Initialize only the newly authorized, isolated synthetic Neon project."""
import json
import secrets
import sys
from pathlib import Path
from dataclasses import replace
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode,quote
import certifi
import psycopg
from psycopg import sql
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.config import ROOT,load_settings
from backend.bootstrap import migrate,seed
source=json.loads((ROOT/".local/neon-owner.json").read_text())["url"]
parsed=urlsplit(source.strip())
if parsed.hostname not in ("ep-icy-hall-b7daw9rk.c-13.us-east-1.aws.neon.tech","ep-icy-hall-b7daw9rk-pooler.c-13.us-east-1.aws.neon.tech"):
    raise ValueError("Refusing to initialize an unrelated database host")
query=dict(parse_qsl(parsed.query))
query.update(sslmode="verify-full",sslrootcert=certifi.where())
owner_url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urlencode(query,quote_via=quote),""))
settings=load_settings()
target=ROOT/".local/neon-base-config.json"
if target.exists():
    settings=type(settings)(**json.loads(target.read_text()))
    password=urlsplit(settings.database_url).password
else:
    password=secrets.token_urlsafe(32)
    # Pooler hostname suffix precedes the regional domain.
    host=parsed.hostname.replace("-pooler","").replace(".c-13.","-pooler.c-13.")
    runtime=urlunsplit((parsed.scheme,"shiftclarity_app:"+quote(password,safe="")+"@"+host,parsed.path,urlencode(query,quote_via=quote),""))
    settings=replace(settings,database_url=runtime)
with psycopg.connect(owner_url) as db:
    if not db.execute("SELECT 1 FROM pg_roles WHERE rolname='shiftclarity_app'").fetchone():
        db.execute(sql.SQL("CREATE ROLE shiftclarity_app LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS").format(sql.Literal(password)))
    migrate(db)
    fixture=ROOT/"handoff/data/synthetic"
    names={"work":"work_records","invoices":"invoice_lines","rules":"rate_rules","batches":"import_batches","excerpts":"source_excerpts","manifest":"manifest"}
    inputs={name:json.loads((fixture/(file+".json")).read_text()) for name,file in names.items()}
    inputs["manifest"]["workspace_label"]="Synthetic pilot workspace"
    seed(db,settings,inputs,json.loads((fixture/"draft_rule.json").read_text()))
    for account in json.loads((ROOT/".local/accounts.json").read_text()):
        if account["org"]!=settings.org_id:
            continue
        db.execute("INSERT INTO memberships VALUES(%s,%s,%s,%s,%s,true) ON CONFLICT DO NOTHING",
                   (settings.issuer,account["id"],settings.org_id,account["actor"],account["roles"]))
target.write_text(json.dumps(settings.__dict__,indent=2))
target.chmod(0o600)
print("New isolated Neon synthetic base initialized with verified TLS and a restricted application role.")
