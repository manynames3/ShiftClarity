"""Assemble confirmed tables into the existing canonical snapshot contract."""
import copy
from datetime import date,timedelta
from decimal import Decimal
from .engine import digest
from .tabular import TableError

RATE_FIELDS=['id','contract_id','facility_id','role','component','rate','currency','effective_from','effective_to','authorization_date','supersedes']

def error(filename,field,message,row=0):
    return {'filename':filename,'worksheet':'','row':row,'field':field,'code':'SOURCE_SELECTION','message':message}

def assemble(period,sources,known,creator,created_at):
    grouped={kind:[] for kind in ['rates','work','invoices']};lineage=[];errors=[];duplicates=0
    for source,result in sources:
        grouped[source['category']].extend(copy.deepcopy(result['records']))
        lineage.extend({**row,'file_id':source['id']} for row in result['lineage'])
        errors.extend(result['errors']);duplicates+=result['duplicates']
    if errors:return {'errors':errors}
    for category in grouped:
        seen={}
        for row in grouped[category]:
            old=seen.get(row['id'])
            if old and old!=row:errors.append(error(category,'id','Conflicting references across files. Correct the source records.'))
            elif old:duplicates+=1
            else:seen[row['id']]=row
        grouped[category]=list(seen.values())
    end=(date.fromisoformat(period['service_to'])+timedelta(days=1)).isoformat()
    reused=[]
    if period.get('use_registered_rates') and not grouped['rates']:
        reused=[r for r in known.values() if (period['facility_id']=='ALL' or r['facility_id']==period['facility_id']) and r['effective_from']<end and (not r.get('effective_to') or r['effective_to']>period['service_from'])]
        grouped['rates']=reused
    if len(grouped['work'])>1000 or len(grouped['invoices'])>2000 or len(grouped['rates'])>150:
        errors.append(error('Files','rows','Use up to 1,000 work rows, 2,000 invoice rows and 150 rate versions per review. Split larger exports by facility and billing period.'))
    if not grouped['work'] or not grouped['rates'] or (not grouped['invoices'] and not (period['invoice_complete'] and period.get('expected_invoice_total') is not None and Decimal(period['expected_invoice_total'])==0)):
        errors.append(error('Files','categories','Supply rates, work and invoices. For a genuinely empty invoice extract, declare complete coverage and enter an independent posted total of zero.'))
    end=(date.fromisoformat(period['service_to'])+timedelta(days=1)).isoformat()
    for kind,rows in grouped.items():
        for row in rows:
            if period['facility_id']!='ALL' and row['facility_id']!=period['facility_id']:
                errors.append(error(kind,'facility_id','A record belongs to a different facility. Select ALL explicitly or correct the file.'))
            if 'service_date' in row and not period['service_from']<=row['service_date']<end:
                errors.append(error(kind,'service_date','A source row is outside the selected billing period. Export the selected scope again.'))
    work=grouped['work'];invoices=grouped['invoices']
    for line in invoices:
        if '_match' in line:
            match=line.pop('_match')
            candidates=[w for w in work if w['facility_id']==line['facility_id'] and all(w[k]==v for k,v in match.items())]
            line['shift_ids']=[candidates[0]['id']] if len(candidates)==1 else []
    total_minutes=sum(w['worked_minutes'] for w in work)
    posted_total=sum((Decimal(line['amount']) for line in invoices if line['state']=='posted'),Decimal(0))
    if period.get('expected_work_hours') is not None and Decimal(period['expected_work_hours'])*60!=total_minutes:
        errors.append(error('Work','source_total','The independently supplied work-hour total does not match parsed rows.'))
    if period.get('expected_invoice_total') is not None and Decimal(period['expected_invoice_total'])!=posted_total:
        errors.append(error('Invoices','source_total','The independently supplied posted-invoice total does not match parsed rows.'))
    excerpts=[];candidates=[];rules=list(reused)
    for source,result in sources:
        if source['category']!='rates':continue
        # One evidence document per rate export, with retained worksheet/row references.
        evidence_hash=digest({'sha':source['content_hash'],'filename':source['filename'],'config':source.get('config')})[:24]
        document_id='DOC-TABLE-'+evidence_hash
        excerpt={'id':'EX-TABLE-'+evidence_hash,'document_id':document_id,'title':source['filename'],
                 'lines':['FICTIONAL RATE EXPORT. Source declarations require independent review.',*[
                     f"{source['filename']} / {item['worksheet']} / row {item['row']}: "+'; '.join(f'{key}: {next(r for r in result["records"] if r["id"]==item["record_id"]).get(key,"")}' for key in RATE_FIELDS)
                     for item in result['lineage']]],'synthetic':True}
        excerpts.append(excerpt)
        for record in result['records']:
            registered=known.get(record['id'])
            if registered:
                if any(record.get(k)!=(registered.get('authorization_date',registered.get('approved_at','')[:10]) if k=='authorization_date' else registered.get(k)) for k in RATE_FIELDS):
                    errors.append(error(source['filename'],'id','An approved rate ID has different terms. Use an explicit new rate version and predecessor.'))
                rules.append(registered)
            else:
                candidate={**record,'state':'pending_approval','source_excerpt_id':excerpt['id'],'author_id':creator,'approver_id':None,'recorded_at':created_at}
                if not any(r['id']==candidate['id'] for r in candidates):candidates.append(candidate)
    if errors:return {'errors':errors}
    # Per-period identity prevents unrelated periods inheriting review decisions.
    identity={'facility':period['facility_id'],'from':period['service_from'],'to':end}
    batch_work='TIME-'+digest(identity)[:20];batch_invoice='INV-'+digest(identity)[:20]
    for row in work:row['batch_id']=batch_work
    for row in invoices:row['batch_id']=batch_invoice
    common={'state':'validated','source_as_of':period['source_as_of'],'service_from':period['service_from'],'service_to_exclusive':end}
    batches=[{**common,'id':batch_work,'source':'work exports','records':len(work),'declared_complete':period['work_complete'],'control_total_minutes':total_minutes},
             {**common,'id':batch_invoice,'source':'invoice exports','records':len(invoices),'declared_complete':period['invoice_complete'],'signed_control_total':format(posted_total,'.2f')}]
    manifest={'dataset_id':'TABLE-'+digest(identity)[:24],'synthetic':True,'version':'table-v1','run_id':'RUN-TABLE-PREVIEW',
              'as_of':period['source_as_of'],'timezone':'UTC','currency':'USD','service_from':period['service_from'],'service_to_exclusive':end,
              'billing_cutoff':period['billing_cutoff'],'invoice_source_as_of':period['source_as_of'],'invoice_coverage_complete':period['invoice_complete'],
              'workspace_label':period['facility_id']+' · Fictional review','note':'Confirmed spreadsheet mappings and declared coverage. No customer data or payment evidence.'}
    warnings=[]
    unmatched=sum(1 for line in invoices if line['state']=='posted' and (not line['shift_ids'] or any(ref not in {w['id'] for w in work} for ref in line['shift_ids'])))
    if unmatched:warnings.append(f'{unmatched} posted invoice line(s) lack unique work references. Affected facilities will remain evidence gaps without estimated differences.')
    if not period['invoice_complete'] or not period['work_complete']:warnings.append('Coverage was not declared complete. Affected work remains unevaluated without a financial estimate.')
    if duplicates:warnings.append(f'{duplicates} identical row(s) with the same native reference were reused once.')
    rules=list({r['id']:r for r in rules}.values())
    return {'errors':[],'normalized':{'work':work,'invoices':invoices,'rules':rules,'batches':batches,'excerpts':[],'manifest':manifest},
            'rate_candidates':candidates,'excerpts':excerpts,'lineage':lineage,'warnings':warnings,
            'summary':{'work_records':len(work),'invoice_lines':len(invoices),'rate_versions':len(grouped['rates']),'new_rates':len(candidates),'work_hours':str(Decimal(total_minutes)/60),'posted_invoice_total':format(posted_total,'.2f'),'duplicates':duplicates}}
