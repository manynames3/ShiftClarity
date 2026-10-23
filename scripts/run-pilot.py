"""Run the secured synthetic app with dedicated PostgreSQL and local OIDC."""
import hashlib
import json
import os
import signal
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
local=ROOT/".local"
local.mkdir(exist_ok=True,mode=0o700)
children=[]
def available(url):
    try:
        with urllib.request.urlopen(url,timeout=2) as response:
            return response.status==200
    except Exception:
        return False
def start(arguments,log,env=None):
    file=(local/log).open("a")
    process=subprocess.Popen(arguments,cwd=ROOT,stdout=file,stderr=file,env=env)
    children.append(process)
    return process
def wait_for(url,process):
    for _ in range(90):
        if available(url):return
        if process.poll() is not None:raise RuntimeError("Service stopped; inspect its local log.")
        time.sleep(1)
    raise RuntimeError("Service startup timed out; inspect its local log.")
try:
    bindir=Path(subprocess.check_output(["pg_config","--bindir"],text=True).strip())
    data=local/"postgres"
    if not data.exists():
        subprocess.run([str(bindir/"initdb"),"-D",str(data),"-A","trust","-U","shiftclarity_local"],check=True,capture_output=True)
    running=subprocess.run([str(bindir/"pg_ctl"),"-D",str(data),"status"],capture_output=True).returncode==0
    if not running:
        subprocess.run([str(bindir/"pg_ctl"),"-D",str(data),"-l",str(local/"postgres.log"),"-o","-h 127.0.0.1 -p 55478","start"],check=True,capture_output=True)
    keycloak=local/"keycloak-26.8.0"
    if not keycloak.exists():
        archive=local/"keycloak.tar.gz"
        if not archive.exists():
            urllib.request.urlretrieve("https://github.com/keycloak/keycloak/releases/download/26.8.0/keycloak-26.8.0.tar.gz",archive)
        expected="9e41da899f838a58cd510fc98ed4f7cadc715aed5683e42aca20a0c9a2a3980a"
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
            raise RuntimeError("Identity provider archive failed checksum verification.")
        with tarfile.open(archive) as file:
            file.extractall(local,filter="data")
    subprocess.run(["node",str(ROOT/"scripts/build-engine.mjs")],check=True,cwd=ROOT)
    subprocess.run([sys.executable,str(ROOT/"scripts/setup-local.py")],check=True,cwd=ROOT)
    subprocess.run(["npm","run","build"],check=True,cwd=ROOT)
    issuer="http://127.0.0.1:5181/realms/shiftclarity/.well-known/openid-configuration"
    if not available(issuer):
        environment=os.environ.copy()
        if not environment.get("JAVA_HOME"):
            for home in ["/opt/homebrew/opt/openjdk@26/libexec/openjdk.jdk/Contents/Home","/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"]:
                if Path(home).exists():
                    environment["JAVA_HOME"]=home
                    break
        identity=start([str(keycloak/"bin/kc.sh"),"start-dev","--http-host=127.0.0.1","--http-port=5181",
                       "--hostname=http://127.0.0.1:5181","--import-realm"],"identity.log",environment)
        wait_for(issuer,identity)
    if available("http://127.0.0.1:5180/health"):
        print("Pilot already running at http://127.0.0.1:5180/pilot/")
    else:
        application_environment=os.environ.copy()
        application_environment.setdefault("SHIFTCLARITY_CONFIG",str(local/"config.json"))
        server=start([sys.executable,"-m","uvicorn","backend.app:create_app","--factory","--host","127.0.0.1",
                      "--port","5180","--no-access-log"],"backend.log",application_environment)
        wait_for("http://127.0.0.1:5180/health",server)
        print("Pilot running at http://127.0.0.1:5180/pilot/ · Individual credentials: .local/accounts.json",flush=True)
        while server.poll() is None:time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    for child in children:
        if child.poll() is None:child.send_signal(signal.SIGTERM)
    for child in children:
        try:child.wait(timeout=15)
        except subprocess.TimeoutExpired:child.kill()
