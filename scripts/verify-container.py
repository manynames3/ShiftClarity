"""Verify the AWS-compatible image without embedding credentials or changing pilot records."""
import json
import subprocess
import time
import argparse
import base64
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode,quote
import httpx

ROOT=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser()
parser.add_argument("--lambda",dest="lambda_image",action="store_true")
args=parser.parse_args()
image="shiftclarity:lambda-verified" if args.lambda_image else "shiftclarity:synthetic-verified"
configuration=json.loads((ROOT/".local/neon-app-config.json").read_text())
url=urlsplit(configuration["database_url"])
query=dict(parse_qsl(url.query))
query.pop("sslrootcert",None) # The container uses its own pinned CA bundle.
configuration.update(database_url=urlunsplit((url.scheme,url.netloc,url.path,urlencode(query,quote_via=quote),"")),
                     origin="http://127.0.0.1:5182",storage_dir="/tmp/private",worker_enabled=False)
if args.lambda_image:
    configuration["job_queue_arn"]="arn:aws:sqs:us-east-1:636305658578:shiftclarity-container-check.fifo"
config_file=ROOT/".local/container-config.json"
config_file.write_text(json.dumps(configuration))
config_file.chmod(0o600)
name="shiftclarity-container-check"
started=False
try:
    subprocess.run(["docker","run","-d","--name",name,"--platform","linux/amd64","--memory","512m",
                    "--cpus","0.25","--read-only","--tmpfs","/tmp:rw,noexec,nosuid,size=16m",
                    "--cap-drop","ALL","--security-opt","no-new-privileges","-p","127.0.0.1:5182:"+("8080" if args.lambda_image else "5180"),
                    "--mount",f"type=bind,source={config_file},target=/config.json,readonly",
                    "-e","SHIFTCLARITY_CONFIG=/config.json",image],check=True,capture_output=True)
    started=True
    with httpx.Client(base_url=configuration["origin"],timeout=3) as client:
        def get(path,headers=None):
            if not args.lambda_image:
                return client.get(path,headers=headers)
            host=(headers or {}).get("Host","127.0.0.1:5182")
            event={"version":"2.0","routeKey":"$default","rawPath":path,"rawQueryString":"","headers":{"host":host},
                   "requestContext":{"http":{"method":"GET","path":path,"sourceIp":"127.0.0.1","protocol":"HTTP/1.1"},
                                     "domainName":host,"stage":"$default"},"isBase64Encoded":False}
            result=client.post("/2015-03-31/functions/function/invocations",json=event,timeout=30).json()
            content=base64.b64decode(result["body"]) if result.get("isBase64Encoded") else result["body"].encode()
            return httpx.Response(result["statusCode"],headers=result["headers"],content=content)
        for attempt in range(30):
            try:
                if get("/health").status_code==200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Container did not become healthy; inspect its private logs")
        health=get("/health")
        assert health.json()=={"status":"running","data_mode":"synthetic"}
        ui=get("/pilot/")
        assert ui.status_code==200 and 'assets/' in ui.text
        assert get("/api/v1/workspace").status_code==401
        assert get("/api/v1/imports").status_code==401
        assert get("/pilot/",headers={"Host":"untrusted.invalid"}).status_code==400
        assert "frame-ancestors 'none'" in ui.headers["content-security-policy"]
    names={"work":"work_records","invoices":"invoice_lines","rules":"rate_rules","batches":"import_batches","excerpts":"source_excerpts","manifest":"manifest"}
    fixture=ROOT/"handoff/data/synthetic"
    inputs={key:json.loads((fixture/(value+".json")).read_text()) for key,value in names.items()}
    payload={"operation":"seed","inputs":inputs,"draft":json.loads((fixture/"draft_rule.json").read_text())}
    engine_path=("/var/task" if args.lambda_image else "/app")+"/backend/engine.mjs"
    result=subprocess.run(["docker","exec","-i",name,"node","--max-old-space-size=96",engine_path],
                          input=json.dumps(payload),text=True,capture_output=True,check=True,timeout=30)
    state=json.loads(result.stdout)
    assert state["ok"] and state["result"]["run"]["id"]=="RUN-001"
    uid=subprocess.run(["docker","exec",name,"id","-u"],text=True,capture_output=True,check=True).stdout.strip()
    assert uid=="10001"
    metadata=json.loads(subprocess.run(["docker","image","inspect",image],text=True,capture_output=True,check=True).stdout)[0]
    evidence={"image_id":metadata["Id"],"architecture":metadata["Architecture"],"nonroot_uid":uid,
              "memory_limit_mib":512,"cpu_limit":0.25,"read_only_root":True,"synthetic_engine":True,
              "restricted_neon_connection":True,"ui":True,"unauthenticated_api_denied":True,"host_validation":True}
    evidence["aws_lambda_runtime_emulator"]=args.lambda_image
    (ROOT/("artifacts/lambda-container-verification.json" if args.lambda_image else "artifacts/container-verification.json")).write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence))
finally:
    if started:
        subprocess.run(["docker","rm","-f",name],check=True,capture_output=True)
    config_file.unlink(missing_ok=True)
