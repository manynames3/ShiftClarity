"""Short-lived parser with bounded bytes, CPU, memory and a scrubbed environment."""
import base64
import json
import resource
import sys

if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(6,6))
    if sys.platform=='linux':resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
    from .tabular import inspect_file,TableError
    try:
        payload=json.loads(sys.stdin.read(1500000))
        result=inspect_file(base64.b64decode(payload['data'],validate=True),payload['filename'],payload['category'],payload.get('sheet'),payload.get('header_row'))
        print(json.dumps({'ok':True,'table':result}))
    except TableError as error:
        print(json.dumps({'ok':False,'code':error.code,'message':str(error)}))
    except Exception:
        print(json.dumps({'ok':False,'code':'PARSER_LIMIT','message':'File could not be safely parsed. Export values only and try a smaller file.'}))
