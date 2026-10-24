"""Period-scoped reviews and evidence-based follow-up; never an invoice/payment ledger."""
import copy
from decimal import Decimal
from psycopg.types.json import Jsonb
from .engine import digest
from .db import store_review

def finding_key(f):
    return '/'.join([f['dataset_id'],f['facility_id'],f['rule_version_id'],f['reason_code'],'over' if Decimal(f['discrepancy_amount'])<0 else 'under'])

def event(db,org,case,actor,action,run_id,data=None):
    db.execute('INSERT INTO case_events(org_id,case_id,actor,action,run_id,data) VALUES(%s,%s,%s,%s,%s,%s)',
               (org,case['id'],actor,action,run_id,Jsonb(data or {})))

def case_identity(run,kind,facility,reference):
    return digest([run['manifest']['service_from'],run['manifest']['service_to_exclusive'],facility,kind,reference])

def sync_cases(db,org,state,actor='SYSTEM'):
    run=state.get('run')
    if not run:return
    m=run['manifest'];records={r['work']['id']:r for r in run['records']};represented=set()
    sources=[('finding',f,f['facility_id'],f['rule_version_id']+'/'+f['reason_code']+('/over' if Decimal(f['discrepancy_amount'])<0 else '/under')) for f in run['findings']]
    for task in run['tasks']:
        for facility in sorted({records[identifier]['work']['facility_id'] for identifier in task['shift_ids']}):
            source={**task,'shift_ids':[i for i in task['shift_ids'] if records[i]['work']['facility_id']==facility]}
            sources.append(('coverage',source,facility,task['reason_code']))
    for kind,source,facility,reference in sources:
        key=case_identity(run,kind,facility,reference);represented.add(key)
        existing=db.execute('SELECT * FROM billing_cases WHERE org_id=%s AND case_key=%s FOR UPDATE',(org,key,)).fetchone()
        amount=source.get('discrepancy_amount');work_ids=sorted(set(source['shift_ids'])|set(existing['work_ids'] if existing else []))
        evidence_hash=source.get('fingerprint') or digest(source)
        if existing:
            reopened=existing['status']=='resolved' or (existing['status']=='dismissed' and existing['evidence_hash'] and existing['evidence_hash']!=evidence_hash)
            if reopened or existing['last_run_id']!=run['id'] or existing['work_ids']!=work_ids or existing['evidence_hash']!=evidence_hash:
                db.execute("UPDATE billing_cases SET last_run_id=%s,source_ref=%s,work_ids=%s,amount=%s,status=%s,evidence_hash=%s,verified_run_id=NULL,version=version+1,updated_at=now() WHERE id=%s",
                           (run['id'],source['id'],Jsonb(work_ids),amount,'open' if reopened else existing['status'],evidence_hash,existing['id']))
                event(db,org,existing,actor,'reopened_by_evidence' if reopened else 'evidence_updated',run['id'],{'amount':amount})
        else:
            review=state.get('reviews',{}).get(finding_key(source),{}) if kind=='finding' else {}
            status={'dismissed':'dismissed','evidence_requested':'awaiting_evidence'}.get(review.get('state'),'open')
            owner=next((e['owner'] for e in reversed(review.get('history',[])) if e.get('owner')),None)
            case=db.execute("""INSERT INTO billing_cases(org_id,case_key,kind,facility_id,service_from,service_to_exclusive,reason_code,work_ids,last_run_id,source_ref,amount,status,owner,evidence_hash)
                               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                            (org,key,kind,facility,m['service_from'],m['service_to_exclusive'],source['reason_code'],Jsonb(work_ids),run['id'],source['id'],amount,status,owner,evidence_hash)).fetchone()
            event(db,org,case,actor,'identified',run['id'],{'amount':amount})
    complete=m['invoice_coverage_complete'] and bool(state['inputs']['batches']) and all(b['declared_complete'] for b in state['inputs']['batches'])
    if not complete or state.get('stale'):return
    old=db.execute("SELECT * FROM billing_cases WHERE org_id=%s AND service_from=%s AND service_to_exclusive=%s AND status NOT IN ('resolved','dismissed') FOR UPDATE",(org,m['service_from'],m['service_to_exclusive'])).fetchall()
    for case in old:
        if case['case_key'] in represented:continue
        affected=[records.get(identifier) for identifier in case['work_ids']]
        eligible={'evaluated_aligned'} if case['kind']=='finding' else {'evaluated_aligned','evaluated_flagged'}
        if affected and all(r and r['work']['facility_id']==case['facility_id'] and r['category'] in eligible for r in affected):
            db.execute("UPDATE billing_cases SET status='resolved',verified_run_id=%s,version=version+1,updated_at=now() WHERE id=%s",(run['id'],case['id']))
            event(db,org,case,actor,'aligned_on_rerun' if case['kind']=='finding' else 'evidence_supplied_on_rerun',run['id'])

def case_for_source(db,state,kind,source_id):
    return db.execute('SELECT * FROM billing_cases WHERE last_run_id=%s AND source_ref=%s AND kind=%s FOR UPDATE',
                      (state['run']['id'],source_id,kind)).fetchall()

def record_review_case(db,org,state,finding_id,action,actor,reason,owner=None):
    for case in case_for_source(db,state,'finding',finding_id):
        status={'dismiss':'dismissed','request_evidence':'awaiting_evidence','reopen':'open'}.get(action,case['status'])
        db.execute('UPDATE billing_cases SET status=%s,owner=COALESCE(%s,owner),version=version+1,updated_at=now() WHERE id=%s',(status,owner,case['id']))
        event(db,org,case,actor,'review_'+action,state['run']['id'],{'reason':reason,'owner':owner})

def case_rows(db,run_id=None):
    if not run_id:return db.execute('SELECT * FROM billing_cases ORDER BY updated_at DESC,id').fetchall()
    source=db.execute('SELECT state FROM review_workspaces WHERE run_id=%s',(run_id,)).fetchone()
    if not source:return []
    run=source['state']['run'];facilities=list({r['work']['facility_id'] for r in run['records']})
    rows=db.execute('SELECT * FROM billing_cases WHERE service_from=%s AND service_to_exclusive=%s AND facility_id=ANY(%s) ORDER BY updated_at DESC,id',
                    (run['manifest']['service_from'],run['manifest']['service_to_exclusive'],facilities)).fetchall()
    identities={case_identity(run,'finding',f['facility_id'],f['rule_version_id']+'/'+f['reason_code']+('/over' if Decimal(f['discrepancy_amount'])<0 else '/under')):f['id'] for f in run['findings']}
    for case in rows:case['selected_source_ref']=identities.get(case['case_key']) if case['kind']=='finding' else next((t['id'] for t in run['tasks'] if t['reason_code']==case['reason_code'] and set(t['shift_ids'])&set(case['work_ids'])),None)
    return rows

def backfill_workflows(db):
    """Owner-only additive migration; immutable calculation/source rows stay untouched."""
    from psycopg.rows import dict_row
    from .fingerprints import compact_state
    with db.cursor(row_factory=dict_row) as cur:
        for org in cur.execute('SELECT id FROM organizations').fetchall():
            cur.execute("SELECT set_config('app.org_id',%s,true)",(org['id'],))
            head=cur.execute('SELECT state FROM workspace_heads WHERE org_id=%s',(org['id'],)).fetchone()
            if not head:continue
            current=compact_state(head['state']);latest=current.get('reviews',{})
            for item in cur.execute('SELECT snapshot,published_at FROM completed_runs WHERE org_id=%s ORDER BY published_at,id',(org['id'],)).fetchall():
                state=compact_state(item['snapshot'])
                for f in state['run']['findings']:
                    review=latest.get(finding_key(f))
                    if review and review['fingerprint']==f['fingerprint']:state['reviews'][finding_key(f)]=copy.deepcopy(review)
                    else:
                        matching=next((r for r in latest.values() if any(e.get('fingerprint')==f['fingerprint'] for e in r.get('history',[]))),None)
                        if matching:
                            last=next(e for e in reversed(matching['history']) if e.get('fingerprint')==f['fingerprint'])
                            events=[copy.deepcopy(e) for e in matching['history'] if e['sequence']<=last['sequence']]
                            status={'confirm':'confirmed','dismiss':'dismissed','request_evidence':'evidence_requested'}.get(last['action'],'needs_review')
                            state['reviews'][finding_key(f)]={'state':status,'fingerprint':f['fingerprint'],'version':last['sequence']+1,'history':events}
                store_review(cur,org['id'],state,item['published_at']);sync_cases(cur,org['id'],state,'MIGRATION')
            store_review(cur,org['id'],current);sync_cases(cur,org['id'],current,'MIGRATION')
