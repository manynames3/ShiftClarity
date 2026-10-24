from contextlib import contextmanager
import psycopg
import certifi
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from .fingerprints import compact_state

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
    row['state']=compact_state(row['state'])
    return row

def store_review(db,org,state,created_at=None):
    if not state.get('run'):return
    state=compact_state(state)
    existing=db.execute('SELECT state FROM review_workspaces WHERE org_id=%s AND run_id=%s',(org,state['run']['id'])).fetchone()
    # Catalog additions belong to the live head; a published period keeps its original source selection.
    if existing:state['inputs']=existing['state']['inputs']
    db.execute("""INSERT INTO review_workspaces(org_id,run_id,state,created_at) VALUES(%s,%s,%s,COALESCE(%s::timestamptz,now()))
                  ON CONFLICT(org_id,run_id) DO UPDATE SET state=EXCLUDED.state,version=review_workspaces.version+1,updated_at=now()""",
               (org,state['run']['id'],Jsonb(state),created_at))

def review_workspace(db,run_id=None,lock=False,current=None):
    current=current or head(db,lock)
    if run_id is None or current['state'].get('run',{}).get('id')==run_id:return current
    row=db.execute('SELECT state,version FROM review_workspaces WHERE run_id=%s'+(' FOR UPDATE' if lock else ''),(run_id,)).fetchone()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404,'Review period not found.')
    row['state']=compact_state(row['state'])
    return row

def save_review(db,org,state):
    current=head(db)
    if current['state'].get('run',{}).get('id')==state['run']['id']:
        save_head(db,org,state)
    else:store_review(db,org,state)

def save_head(db, org, state):
    state=compact_state(state)
    db.execute("UPDATE workspace_heads SET state=%s,version=version+1 WHERE org_id=%s",(Jsonb(state),org))
    store_review(db,org,state)
