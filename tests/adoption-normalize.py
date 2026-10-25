import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from backend.tabular import inspect_file
from backend.table_mapping import normalize_table
result={}
for kind in ['work','invoices','rates']:
 path=Path('public/examples/agency-evaluation')/(kind+'.csv');t=inspect_file(path.read_bytes(),path.name,kind)
 cfg={'mapping':t['mapping'],'constants':{},'value_maps':t['value_maps'],'date_format':'ISO','decimal_format':'dot','time_unit':'minutes','end_date_mode':'exclusive','confirmed':True}
 out=normalize_table(t,kind,cfg,path.name,'a'*64)
 assert not out['errors'],out['errors']
 result[kind]=out['records']
print(json.dumps(result))
