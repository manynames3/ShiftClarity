import hashlib
import json
import subprocess
import threading
from .config import ROOT
from .fingerprints import compact_state

class EngineError(Exception):
    pass

PARSERS=threading.BoundedSemaphore(2)

def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()

def compute(operation, **payload):
    if 'state' in payload:payload['state']=compact_state(payload['state'])
    try:
        with PARSERS:
            result = subprocess.run(
                ["node","--max-old-space-size=96",str(ROOT/"backend/engine.mjs")],
                input=json.dumps({"operation":operation,**payload}),text=True,
                # Leave room for Node's first start in Lambda and for the 29-second HTTP limit.
                capture_output=True,timeout=20,check=False,
            )
        response = json.loads(result.stdout)
        if result.returncode or not response.get("ok"):
            allowed={"VALIDATION_OR_CONFLICT","INVALID_JSON","UNSUPPORTED_FIELDS","SOURCE_CONTROLS","INVALID_SCHEMA"}
            raise EngineError(response.get("error") if response.get("error") in allowed else "VALIDATION_OR_CONFLICT")
        return response["result"]
    except (subprocess.TimeoutExpired, ValueError, OSError):
        raise EngineError("PARSER_LIMIT_OR_UNAVAILABLE") from None
