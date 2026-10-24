"""Compact legacy evidence references without changing immutable source snapshots."""
import copy
import hashlib

def fingerprint(value):
    if isinstance(value,str) and (value.startswith('ev1:') or value.startswith('{') or value.startswith('[')):
        return 'sha256:'+hashlib.sha256(value.encode()).hexdigest()
    return value

def compact_state(value):
    state=copy.deepcopy(value)
    def visit(item):
        if isinstance(item,dict):
            for key,value in item.items():
                if key=='fingerprint':item[key]=fingerprint(value)
                else:visit(value)
        elif isinstance(item,list):
            for value in item:visit(value)
    visit(state)
    return state
