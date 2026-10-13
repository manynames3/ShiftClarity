import json
import copy
import re
import secrets
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator
from psycopg.types.json import Jsonb
from .config import ROOT, load_settings
from .db import transaction, audit, head, save_head
from .engine import compute, digest, EngineError
from .storage import PrivateStorage
from . import auth, jobs
from .imports import receive

class StrictBody(BaseModel):
    model_config=ConfigDict(extra="forbid",strict=True)
    @field_validator("reason",check_fields=False)
    @classmethod
    def reason_is_specific(cls,value):
        if len(value.strip())<3 or any(ord(c)<32 and c not in "\n\t" for c in value):
            raise ValueError("Specific reason required")
        return value.strip()

class Decision(StrictBody):
    action: Literal["confirm","dismiss","request_evidence","reopen"]
    reason: str=Field(min_length=3,max_length=2000)
    expected_fingerprint: str=Field(max_length=1024*1024)
    expected_version: StrictInt=Field(ge=1)
    run_id: str=Field(max_length=80)
    owner: str|None=Field(default=None,max_length=80)

class Approval(StrictBody):
    action: Literal["approve","reject"]
    reason: str=Field(min_length=3,max_length=2000)
    expected_version: StrictInt=Field(ge=1)

class RunRequest(StrictBody):
    import_id: str=Field(max_length=80)

class TaskRequest(StrictBody):
    task_id: str=Field(max_length=80)
    run_id: str=Field(max_length=80)
    reason: str=Field(min_length=3,max_length=2000)
    owner: str=Field(min_length=1,max_length=80)

class Proposal(StrictBody):
    supersedes: str=Field(max_length=80)
    source_excerpt_id: str=Field(max_length=80)
    rate: str=Field(pattern=r"^\d{1,8}(\.\d{1,4})?$")
    effective_from: str=Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    expected_version: StrictInt=Field(ge=1)

class SourceDocument(StrictBody):
    title: str=Field(min_length=3,max_length=200)
    text: str=Field(min_length=10,max_length=2000)
    synthetic: Literal[True]

def now():
    return datetime.now(timezone.utc).isoformat()

def request_key(request):
    value=request.headers.get("idempotency-key","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,80}",value):
        raise HTTPException(400,"An idempotency key of 16–80 safe characters is required.")
    return value

def write_once(db,member,key,payload,operation):
    fingerprint=digest(payload)
    receipt=db.execute("SELECT request_hash,response FROM write_receipts WHERE actor=%s AND request_key=%s",
                       (member["actor"],key)).fetchone()
    if receipt:
        if receipt["request_hash"]!=fingerprint:
            raise HTTPException(409,"Idempotency key conflicts with an earlier action.")
        return receipt["response"]
    response=operation()
    db.execute("INSERT INTO write_receipts VALUES(%s,%s,%s,%s,%s)",
               (member["org_id"],member["actor"],key,fingerprint,Jsonb(response)))
    return response

def check_runtime(settings):
    auth.verify_cloud_mfa(settings)
    with transaction(settings) as db:
        privileges=db.execute("SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user").fetchone()
        owner=db.execute("SELECT tableowner=current_user AS owner FROM pg_tables WHERE tablename='workspace_heads'").fetchone()
        if privileges["rolsuper"] or privileges["rolbypassrls"] or not owner or owner["owner"]:
            raise ValueError("Use the restricted runtime database login")

def create_app(settings=None):
    settings=settings or load_settings()
    settings.validate()
    storage=PrivateStorage(settings)
    stop=threading.Event()
    wake=threading.Event()
    @asynccontextmanager
    async def lifespan(app):
        check_runtime(settings)
        thread=threading.Thread(target=jobs.loop,args=(settings,stop,wake),daemon=True)
        if settings.worker_enabled:
            thread.start()
        yield
        stop.set()
        wake.set()
        if settings.worker_enabled:
            thread.join(timeout=15)
    app=FastAPI(title="ShiftClarity synthetic pilot API",version="0.4.0",lifespan=lifespan,docs_url=None,redoc_url=None)

    @app.middleware("http")
    async def security_headers(request,call_next):
        if request.headers.get("host")!=settings.origin.split("://",1)[1] and request.url.path!="/health":
            return JSONResponse({"detail":"Invalid host"},400)
        length=request.headers.get("content-length","0")
        if not length.isdigit() or int(length)>1024*1024:
            return JSONResponse({"detail":"Request exceeds 1 MiB limit."},413)
        response=await call_next(request)
        response.headers.update({
            "Cache-Control":"no-store","X-Content-Type-Options":"nosniff",
            "Referrer-Policy":"no-referrer","X-Frame-Options":"DENY",
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
            "Permissions-Policy":"camera=(), microphone=(), geolocation=()",
        })
        # Only build assets are public. Auth, records and downloads always remain no-store.
        if request.url.path.startswith("/assets/") and response.status_code==200:
            response.headers["Cache-Control"]="public, max-age=31536000, immutable"
        if settings.cloud:
            response.headers["Strict-Transport-Security"]="max-age=31536000"
        return response

    @app.exception_handler(RequestValidationError)
    async def bad_input(request,error):
        return JSONResponse({"detail":"Invalid request fields or values."},422)

    @app.exception_handler(EngineError)
    async def bad_engine(request,error):
        return JSONResponse({"detail":"Validation or evidence conflict. Refresh and check the input."},409)

    @app.exception_handler(Exception)
    async def server_failure(request,error):
        return JSONResponse({"detail":"Service unavailable. No partial result was published."},503)

    @app.get("/health")
    def health():
        return {"status":"running","data_mode":"synthetic"}

    @app.get("/auth/login")
    def login():
        return auth.login(settings)

    @app.get("/auth/callback")
    def callback(request:Request):
        return auth.callback(settings,request)

    @app.get("/auth/continue")
    def continue_login(request:Request):
        return auth.continue_login(settings,request)

    @app.post("/auth/logout")
    def logout(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            db.execute("DELETE FROM sessions WHERE digest=%s",(digest(request.cookies[auth.cookie_name(settings,auth.COOKIE)].encode()),))
            audit(db,member["org_id"],member["actor"],"signed_out","session")
        response=JSONResponse({"signed_out":True,"logout_url":auth.logout_url(settings)})
        response.delete_cookie(auth.cookie_name(settings,auth.COOKIE),path="/",secure=settings.cloud,httponly=True,samesite="lax")
        return response

    @app.get("/api/v1/session")
    def session(request:Request):
        member=auth.principal(settings,request)
        return {"actor":member["actor"],"roles":member["roles"],"csrf":member["csrf"],"synthetic":True}

    @app.get("/api/v1/workspace")
    def workspace(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            return {**head(db),"catalog":{
                "rules":[row["content"] for row in db.execute("SELECT content FROM rule_versions ORDER BY id").fetchall()],
                "excerpts":[row["content"] for row in db.execute("SELECT content FROM documents ORDER BY id").fetchall()]
            }}

    @app.get("/api/v1/rules/{rule_id}")
    def rule_resource(rule_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            current=head(db)
            if current["state"]["draft"]["id"]==rule_id:
                return {"rule":current["state"]["draft"],"version":current["version"]}
            row=db.execute("SELECT content FROM rule_versions WHERE id=%s",(rule_id,)).fetchone()
            if not row:
                raise HTTPException(404,"Rule not found.")
            return {"rule":row["content"],"immutable":True}

    @app.get("/api/v1/runs/latest")
    def latest(request:Request):
        return workspace(request)["state"]["run"]

    @app.get("/api/v1/runs/{run_id}")
    @app.get("/api/v1/runs/{run_id}/findings")
    @app.get("/api/v1/runs/{run_id}/coverage")
    def run_resource(run_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            row=db.execute("SELECT snapshot FROM completed_runs WHERE id=%s",(run_id,)).fetchone()
            if not row:
                raise HTTPException(404,"Run not found.")
            result=row["snapshot"]["run"]
            return result["findings"] if request.url.path.endswith("/findings") else result["coverage"] if request.url.path.endswith("/coverage") else result

    @app.get("/api/v1/findings/{finding_id}")
    def finding(finding_id:str,request:Request):
        state=workspace(request)["state"]
        result=next((f for f in state["run"]["findings"] if f["id"]==finding_id),None)
        if not result:
            raise HTTPException(404,"Finding not found.")
        return result

    @app.post("/api/v1/findings/{finding_id}/decisions")
    def decide(finding_id:str,body:Decision,request:Request):
        member=auth.principal(settings,request,"reviewer")
        key=request_key(request)
        with transaction(settings,member["org_id"]) as db:
            current=head(db,True)
            state=current["state"]
            def apply():
                if state["run"]["id"]!=body.run_id or state["stale"]:
                    raise HTTPException(409,"Results changed or are stale. Refresh before reviewing.")
                if body.owner and not db.execute("SELECT 1 FROM memberships WHERE org_id=%s AND actor=%s AND active",(member["org_id"],body.owner)).fetchone():
                    raise HTTPException(422,"Choose an active workspace member as owner.")
                updated=compute("decide",state=state,finding=finding_id,action=body.action,reason=body.reason,
                                fingerprint=body.expected_fingerprint,version=body.expected_version,owner=body.owner,
                                actor=member["actor"],timestamp=now())
                save_head(db,member["org_id"],updated)
                audit(db,member["org_id"],member["actor"],"finding_"+body.action,body.run_id+"/"+finding_id,{"version":body.expected_version+1})
                return {"state":updated,"version":current["version"]+1}
            return write_once(db,member,key,{"resource":finding_id,**body.model_dump()},apply)

    @app.post("/api/v1/tasks")
    def task(body:TaskRequest,request:Request):
        member=auth.principal(settings,request,"reviewer")
        with transaction(settings,member["org_id"]) as db:
            current=head(db,True)
            state=current["state"]
            def apply():
                if state["run"]["id"]!=body.run_id or state["stale"] or not any(t["id"]==body.task_id for t in state["run"]["tasks"]):
                    raise HTTPException(409,"Coverage task changed. Refresh first.")
                if not db.execute("SELECT 1 FROM memberships WHERE org_id=%s AND actor=%s AND active",(member["org_id"],body.owner)).fetchone():
                    raise HTTPException(422,"Choose an active workspace member.")
                state["localTasks"].append({"sequence":len(state["localTasks"])+1,"action":"request_evidence","reason":body.reason,
                                          "owner":body.owner,"actor":member["actor"],"timestamp":now(),"fingerprint":body.task_id})
                save_head(db,member["org_id"],state)
                audit(db,member["org_id"],member["actor"],"coverage_task",body.task_id)
                return {"state":state,"version":current["version"]+1}
            return write_once(db,member,request_key(request),body.model_dump(),apply)

    @app.get("/api/v1/members")
    def members(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            return db.execute("SELECT actor,roles FROM memberships WHERE org_id=%s AND active ORDER BY actor",(member["org_id"],)).fetchall()

    @app.post("/api/v1/documents")
    def source_document(body:SourceDocument,request:Request):
        member=auth.principal(settings,request,"author")
        if any(ord(c)<32 and c not in "\n\t" for c in body.text+body.title):
            raise HTTPException(422,"Source text contains unsupported control characters.")
        with transaction(settings,member["org_id"]) as db:
            current=head(db,True)
            state=current["state"]
            def apply():
                if len(state["inputs"]["excerpts"])>=100:
                    raise HTTPException(429,"Source excerpt limit reached.")
                identifier="DOC-"+uuid.uuid4().hex
                excerpt={"id":"EX-"+uuid.uuid4().hex,"document_id":identifier,"title":body.title,
                         "lines":["SYNTHETIC DOCUMENT. Not a customer agreement.",*body.text.splitlines()],"synthetic":True}
                object_key=member["org_id"]+"/accepted/"+uuid.uuid4().hex
                storage.put(object_key,json.dumps(excerpt).encode())
                db.execute("INSERT INTO documents(org_id,id,content,object_key,content_hash) VALUES(%s,%s,%s,%s,%s)",
                           (member["org_id"],identifier,Jsonb(excerpt),object_key,digest(excerpt)))
                state["inputs"]["excerpts"].append(excerpt)
                save_head(db,member["org_id"],state)
                audit(db,member["org_id"],member["actor"],"source_registered",identifier)
                return {"state":state,"version":current["version"]+1}
            return write_once(db,member,request_key(request),body.model_dump(),apply)

    @app.get("/api/v1/template")
    def template(request:Request):
        member=auth.principal(settings,request,"importer")
        with transaction(settings,member["org_id"]) as db:
            inputs=head(db)["state"]["inputs"]
            return Response(json.dumps(inputs,indent=2),media_type="application/json",headers={"Content-Disposition":'attachment; filename="synthetic-template.json"'})

    @app.post("/api/v1/rules/{rule_id}/approval")
    def approve(rule_id:str,body:Approval,request:Request):
        member=auth.principal(settings,request,"approver")
        with transaction(settings,member["org_id"]) as db:
            current=head(db,True)
            state=current["state"]
            def apply():
                if rule_id!=state["draft"]["id"]:
                    raise HTTPException(404,"Draft not found.")
                if body.expected_version!=current["version"]:
                    raise HTTPException(409,"Draft version changed. Refresh and review again.")
                if state["draft"]["author_id"]==member["actor"]:
                    raise HTTPException(403,"A different person must approve this rule.")
                approval_state=copy.deepcopy(state)
                approval_state["inputs"]["rules"]=[row["content"] for row in db.execute("SELECT content FROM rule_versions").fetchall()]
                approval_state["inputs"]["excerpts"]=[row["content"] for row in db.execute("SELECT content FROM documents").fetchall()]
                updated=compute(body.action,state=approval_state,actor=member["actor"],reason=body.reason,timestamp=now())
                updated["inputs"]=state["inputs"]
                if body.action=="approve":
                    db.execute("INSERT INTO rule_versions VALUES(%s,%s,%s)",(member["org_id"],updated["draft"]["id"],Jsonb(updated["draft"])))
                save_head(db,member["org_id"],updated)
                audit(db,member["org_id"],member["actor"],"rule_"+body.action,rule_id)
                return {"state":updated,"version":current["version"]+1}
            return write_once(db,member,request_key(request),{"resource":rule_id,**body.model_dump()},apply)

    @app.post("/api/v1/rules/drafts")
    def propose(body:Proposal,request:Request):
        member=auth.principal(settings,request,"author")
        with transaction(settings,member["org_id"]) as db:
            current=head(db,True)
            state=current["state"]
            def apply():
                from datetime import date
                if body.expected_version!=current["version"]:
                    raise HTTPException(409,"Workspace changed. Refresh first.")
                if state["draft"]["state"]=="pending_approval":
                    raise HTTPException(409,"Review or reject the existing pending draft first.")
                prior=db.execute("SELECT content FROM rule_versions WHERE id=%s",(body.supersedes,)).fetchone()
                if not prior or not db.execute("SELECT 1 FROM documents WHERE content->>'id'=%s",(body.source_excerpt_id,)).fetchone():
                    raise HTTPException(422,"Select a registered predecessor and source excerpt.")
                try:
                    effective=date.fromisoformat(body.effective_from)
                    if effective<=date.fromisoformat(prior["content"]["effective_from"]):
                        raise ValueError()
                except ValueError:
                    raise HTTPException(422,"Effective date must follow the predecessor start.") from None
                draft={**prior["content"],"id":"RULE-"+uuid.uuid4().hex+"-DRAFT","supersedes":body.supersedes,
                       "rate":format(__import__("decimal").Decimal(body.rate),".4f"),"effective_from":body.effective_from,"effective_to":None,
                       "source_excerpt_id":body.source_excerpt_id,"author_id":member["actor"],"approver_id":None,
                       "state":"pending_approval","recorded_at":now()}
                draft.pop("approved_at",None)
                state["draft"]=draft
                save_head(db,member["org_id"],state)
                audit(db,member["org_id"],member["actor"],"rule_proposed",draft["id"])
                return {"state":state,"version":current["version"]+1}
            return write_once(db,member,request_key(request),body.model_dump(),apply)

    @app.post("/api/v1/imports")
    async def upload(request:Request):
        member=auth.principal(settings,request,"importer")
        key=request_key(request)
        if request.headers.get("content-type","").split(";")[0]!="application/json" or request.headers.get("x-data-classification")!="synthetic":
            raise HTTPException(415,"Only attested synthetic normalized JSON bundles are accepted.")
        data=bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data)>1024*1024:
                raise HTTPException(413,"File exceeds 1 MiB.")
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(receive,settings,storage,member,bytes(data),key)

    @app.get("/api/v1/imports/{import_id}")
    def import_status(import_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            row=db.execute("SELECT id,status,diagnostic,content_hash,created_at,expires_at FROM imports WHERE id=%s",(import_id,)).fetchone()
            if not row:
                raise HTTPException(404,"Import not found.")
            return row

    @app.get("/api/v1/imports")
    def import_list(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            return db.execute("SELECT id,status,diagnostic,created_at,expires_at FROM imports ORDER BY created_at DESC LIMIT 30").fetchall()

    @app.post("/api/v1/runs")
    def queue(body:RunRequest,request:Request,background_tasks:BackgroundTasks):
        member=auth.principal(settings,request,"importer")
        key=request_key(request)
        with transaction(settings,member["org_id"]) as db:
            head(db,True)
            previous=db.execute("SELECT id,import_id,status FROM jobs WHERE request_key=%s",(key,)).fetchone()
            if previous:
                if previous["import_id"]!=body.import_id:
                    raise HTTPException(409,"Run idempotency key conflicts with earlier source selection.")
                if previous["status"] in ("queued","reconciling"):
                    jobs.notify(settings,previous["id"])
                    background_tasks.add_task(wake.set)
                return previous
            if not db.execute("SELECT 1 FROM imports WHERE id=%s AND status='validated' AND expires_at>now()",(body.import_id,)).fetchone():
                raise HTTPException(404,"Validated unexpired import not found.")
            identifier="RUN-"+uuid.uuid4().hex
            db.execute("INSERT INTO jobs(id,org_id,request_key,import_id,actor,status) VALUES(%s,%s,%s,%s,%s,'queued')",
                       (identifier,member["org_id"],key,body.import_id,member["actor"]))
            audit(db,member["org_id"],member["actor"],"run_queued",identifier)
            # Send before commit; SQS retries if delivery precedes the committed job.
            jobs.notify(settings,identifier)
            background_tasks.add_task(wake.set)
            return {"id":identifier,"status":"queued","import_id":body.import_id}

    @app.get("/api/v1/jobs/{job_id}")
    def job_status(job_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            job=db.execute("SELECT id,status,attempts,diagnostic,import_id FROM jobs WHERE id=%s",(job_id,)).fetchone()
            if not job:
                raise HTTPException(404,"Job not found.")
            return job

    @app.get("/api/v1/runs/{run_id}/review-export")
    def export(run_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            state=head(db)["state"]
            if state["run"]["id"]!=run_id:
                raise HTTPException(409,"Export the current reviewed run.")
            text=compute("export",state=state)
            audit(db,member["org_id"],member["actor"],"review_export",run_id)
            return Response(text,media_type="text/csv",headers={"Content-Disposition":'attachment; filename="ShiftClarity-reviewed-findings.csv"'})

    @app.get("/api/v1/documents/{document_id}/access")
    def document(document_id:str,request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            registered=db.execute("SELECT content FROM documents WHERE id=%s",(document_id,)).fetchone()
            if not registered:
                raise HTTPException(404,"Document not found.")
            audit(db,member["org_id"],member["actor"],"document_download",document_id)
            return Response(json.dumps(registered["content"]),media_type="application/json",headers={"Content-Disposition":'attachment; filename="source-excerpt.json"'})

    @app.get("/api/v1/imports/{import_id}/source")
    def download(import_id:str,request:Request):
        member=auth.principal(settings,request,"importer")
        with transaction(settings,member["org_id"]) as db:
            row=db.execute("SELECT object_key FROM imports WHERE id=%s AND status='validated' AND expires_at>now()",(import_id,)).fetchone()
            if not row:
                raise HTTPException(404,"Accepted unexpired source not found.")
            data=storage.get(row["object_key"])
            audit(db,member["org_id"],member["actor"],"source_download",import_id)
            return Response(data,media_type="application/json",headers={"Content-Disposition":'attachment; filename="accepted-synthetic-source.json"'})

    @app.get("/api/v1/audit")
    def audit_log(request:Request):
        member=auth.principal(settings,request)
        with transaction(settings,member["org_id"]) as db:
            return db.execute("SELECT sequence,actor,action,resource,created_at FROM audit_events ORDER BY sequence DESC LIMIT 100").fetchall()

    if (ROOT/"dist/assets").exists():
        app.mount("/assets",StaticFiles(directory=ROOT/"dist/assets"),name="assets")
        app.mount("/brand",StaticFiles(directory=ROOT/"dist/brand"),name="brand")
        @app.get("/")
        @app.get("/pilot/")
        @app.get("/demo/")
        def frontend():
            return FileResponse(ROOT/"dist/index.html")
    return app
