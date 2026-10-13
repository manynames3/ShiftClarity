from contextlib import contextmanager
import psycopg
import certifi
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

@contextmanager
def transaction(settings, org_id=None):
    with psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=5,**({"sslrootcert":certifi.where()} if "sslmode=verify-full" in settings.database_url else {})) as connection:
        connection.execute("SET LOCAL statement_timeout = '15000ms'")
        if org_id:
            connection.execute("SELECT set_config('app.org_id',%s,true)", (org_id,))
        yield connection

def audit(db, org, actor, action, resource, metadata=None):
    db.execute("INSERT INTO audit_events(org_id,actor,action,resource,metadata) VALUES(%s,%s,%s,%s,%s)",
               (org,actor,action,resource,Jsonb(metadata or {})))

def head(db, lock=False):
    row = db.execute("SELECT state,version FROM workspace_heads" + (" FOR UPDATE" if lock else "")).fetchone()
    if not row:
        raise LookupError("Workspace has not been initialized")
    return row

def save_head(db, org, state):
    db.execute("UPDATE workspace_heads SET state=%s,version=version+1 WHERE org_id=%s",(Jsonb(state),org))
