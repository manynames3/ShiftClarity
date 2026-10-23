import json
import uuid
from fastapi import HTTPException
from psycopg.types.json import Jsonb
from .db import transaction, audit, head, save_head
from .engine import compute, digest, EngineError

HELP={
 "INVALID_JSON":"Use a valid UTF-8 JSON bundle from the template.",
 "UNSUPPORTED_FIELDS":"Remove fields outside the template. Names, patient and clinical fields are not allowed.",
 "SOURCE_CONTROLS":"Reconcile source row counts, worked minutes and signed invoice totals before importing.",
 "INVALID_SCHEMA":"Check required fields, IDs, dates, decimal strings and supported values against the template.",
 "SYNTHETIC_ONLY":"Only fictional records are authorized in this build.",
 "UNAPPROVED_RULE_VERSION":"Register the source and obtain independent approval for the exact rule version before importing.",
 "UNREVIEWED_SOURCE":"Register the exact fictional source excerpt before using it in a snapshot.",
 "CONFLICTING_SOURCE_REVISION":"The same work ID/revision has different content. Supply the corrected source revision instead of rewriting it.",
 "PARSER_LIMIT_OR_UNAVAILABLE":"Validation exceeded its resource limit or was unavailable. Retry a smaller normalized bundle."
}

def receipt(row):
    result={key:row[key] for key in ("id","status","content_hash","diagnostic") if key in row}
    if row.get("diagnostic"):
        result["help"]=HELP.get(row["diagnostic"],"Check the normalized template, source controls and registered rule versions.")
    return result

def failed_attempt(db,member,key,row,state,initial=False,invalidate=True):
    # Content deduplication must not hide a new failed attempt after a recovered run.
    fingerprint=digest({"resource":"failed-import","content_hash":row["content_hash"]})
    saved=db.execute("SELECT request_hash,response FROM write_receipts WHERE actor=%s AND request_key=%s",
                     (member["actor"],key)).fetchone()
    if saved:
        if saved["request_hash"]!=fingerprint:
            raise HTTPException(409,"Idempotency key conflicts with an earlier action.")
        return saved["response"]
    response=receipt(row)
    # Older rejected imports already record the original key, even without an attempt receipt.
    if initial or row.get("request_key")!=key:
        if invalidate:
            state.update(stale=bool(state["run"]),error=HELP.get(row["diagnostic"],"Import rejected. Check the template."),importState="failed")
            save_head(db,member["org_id"],state)
        audit(db,member["org_id"],member["actor"],"import_rejected",row["id"],{"code":row["diagnostic"]})
    db.execute("INSERT INTO write_receipts VALUES(%s,%s,%s,%s,%s)",
               (member["org_id"],member["actor"],key,fingerprint,Jsonb(response)))
    return response

def conflicting_revisions(db,normalized):
    conflicts=[]
    for kind in ('work','invoices'):
        records=normalized[kind];ids=list({r['id'] for r in records})
        rows=db.execute('SELECT external_id,revision,content_hash FROM source_revisions WHERE kind=%s AND external_id=ANY(%s)',(kind,ids)).fetchall() if ids else []
        prior={(r['external_id'],r['revision']):r['content_hash'] for r in rows}
        for record in records:
            identity={k:v for k,v in record.items() if k!='batch_id'}
            revision=record['source_revision'] if kind=='work' else digest(identity)
            if (record['id'],revision) in prior and prior[(record['id'],revision)]!=digest(identity):conflicts.append((kind,record['id']))
    return conflicts

def receive(settings,storage,member,data,key,invalidate_on_failure=True):
    content_hash=digest(data)
    import_id="IMP-"+uuid.uuid4().hex
    object_key=settings.org_id+"/quarantine/"+uuid.uuid4().hex
    with transaction(settings,member["org_id"]) as db:
        # Organization lock makes overlapping requests and receipt checks atomic.
        state=head(db,True)["state"]
        existing=db.execute("SELECT id,request_key,content_hash,status,diagnostic,object_key FROM imports WHERE request_key=%s OR content_hash=%s",
                            (key,content_hash)).fetchall()
        for row in existing:
            if row["request_key"]==key and row["content_hash"]!=content_hash:
                raise HTTPException(409,"Idempotency key was already used for different content.")
        if existing:
            row=existing[0]
            if row["status"]!="quarantined":
                return failed_attempt(db,member,key,row,state,invalidate=invalidate_on_failure) if row["status"]=="failed" else receipt(row)
            import_id,object_key=row["id"],row["object_key"]
        else:
            count=db.execute("SELECT count(*) AS n FROM imports WHERE created_at>now()-interval '1 hour'").fetchone()["n"]
            if count>=20:
                raise HTTPException(429,"Import limit reached. Try again after an hour.")
            storage.put(object_key,data)
            try:
                db.execute("INSERT INTO imports(id,org_id,request_key,content_hash,object_key,status) VALUES(%s,%s,%s,%s,%s,'quarantined')",
                           (import_id,member["org_id"],key,content_hash,object_key))
                audit(db,member["org_id"],member["actor"],"import_quarantined",import_id)
            except Exception:
                storage.delete(object_key)
                raise
    try:
        # File extension or browser preview never establishes trusted content.
        normalized=compute("validate",text=data.decode("utf-8"))
        if normalized["manifest"]["synthetic"] is not True:
            raise EngineError("SYNTHETIC_ONLY")
        normalized["manifest"]["workspace_label"]="Synthetic pilot workspace"
        with transaction(settings,member["org_id"]) as db:
            state=head(db,True)["state"]
            current=db.execute("SELECT id,request_key,status,content_hash,diagnostic FROM imports WHERE id=%s",(import_id,)).fetchone()
            if current["status"]!="quarantined":
                return failed_attempt(db,member,key,current,state,invalidate=invalidate_on_failure) if current["status"]=="failed" else receipt(current)
            trusted=db.execute("SELECT content FROM rule_versions").fetchall()
            known={r["content"]["id"]:r["content"] for r in trusted}
            for rule in normalized["rules"]:
                if rule["id"] not in known or digest(rule)!=digest(known[rule["id"]]):
                    raise EngineError("UNAPPROVED_RULE_VERSION")
            for excerpt in normalized["excerpts"]:
                registered=db.execute("SELECT content FROM documents WHERE id=%s",(excerpt["document_id"],)).fetchone()
                old=registered["content"] if registered else None
                if not old or digest(excerpt)!=digest(old):
                    raise EngineError("UNREVIEWED_SOURCE")
            if conflicting_revisions(db,normalized):raise EngineError('CONFLICTING_SOURCE_REVISION')
            for kind in ("work","invoices"):
                records=normalized[kind]
                revisions=[]
                lineage=[]
                for record in records:
                    identity={k:v for k,v in record.items() if k!="batch_id"}
                    revision=record["source_revision"] if kind=="work" else digest(identity)
                    hashed=digest(identity)
                    revisions.append((member["org_id"],kind,record["id"],revision,hashed,Jsonb(identity)))
                    lineage.append((member["org_id"],import_id,kind,record["id"],revision))
                with db.cursor() as cursor:
                    cursor.executemany("INSERT INTO source_revisions VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",revisions)
                    cursor.executemany("INSERT INTO source_lineage VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",lineage)
            accepted_key=object_key.replace("/quarantine/","/accepted/")
            storage.put(accepted_key,data)
            db.execute("UPDATE imports SET status='validated',normalized=%s,object_key=%s WHERE id=%s",(Jsonb(normalized),accepted_key,import_id))
            audit(db,member["org_id"],member["actor"],"import_validated",import_id,{"sha256":content_hash})
        storage.delete(object_key)
        return {"id":import_id,"status":"validated","content_hash":content_hash}
    except (EngineError,UnicodeError) as error:
        # Do not retain rejected bytes or copy parser content into diagnostics/logs.
        storage.delete(object_key)
        with transaction(settings,member["org_id"]) as db:
            state=head(db,True)["state"]
            current=db.execute("SELECT id,request_key,status,content_hash,diagnostic FROM imports WHERE id=%s",(import_id,)).fetchone()
            if current["status"]!="quarantined":
                return failed_attempt(db,member,key,current,state,invalidate=invalidate_on_failure) if current["status"]=="failed" else receipt(current)
            code=str(error) if isinstance(error,EngineError) and str(error) in HELP else "INVALID_SCHEMA"
            db.execute("UPDATE imports SET status='failed',diagnostic=%s WHERE id=%s",(code,import_id))
            return failed_attempt(db,member,key,{**current,"status":"failed","diagnostic":code},state,initial=True,invalidate=invalidate_on_failure)
