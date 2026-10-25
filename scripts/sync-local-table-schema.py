"""Generate public mapping metadata from the private adapter, never source records."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.tabular import FIELDS,VALUES,DENIED
content=json.dumps({'fields':FIELDS,'values':VALUES,'denied':sorted(DENIED)},indent=2)+'\n'
path=ROOT/'src/adapters/table-schema.json'
if '--check' in sys.argv:
    if path.read_text()!=content:raise SystemExit('Mapping schema drift. Run scripts/sync-local-table-schema.py and review the metadata change.')
else:path.write_text(content)
