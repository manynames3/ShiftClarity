"""Confirmed column/value mappings to canonical records; exact decimals only."""
import csv
import io
import re
from datetime import date,datetime,timedelta
from decimal import Decimal,InvalidOperation
from .engine import digest
from .tabular import FIELDS,VALUES,TableError,time_unit_hint

DATE_FORMATS={"ISO":"%Y-%m-%d","MDY":"%m/%d/%Y","DMY":"%d/%m/%Y"}

def identifier(value):
    value=str(value).strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',value):raise ValueError('Use a stable reference ID of up to 80 letters, digits, underscores or hyphens.')
    return value

def day(value,convention):
    value=str(value).strip()
    # Excel date-typed cells are already unambiguous ISO values.
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?)?',value):
        datetime.fromisoformat(value.replace('Z','+00:00'))
        return date.fromisoformat(value[:10]).isoformat()
    if convention not in DATE_FORMATS:raise ValueError('Choose ISO, month/day/year or day/month/year.')
    try:return datetime.strptime(value,DATE_FORMATS[convention]).date().isoformat()
    except ValueError:raise ValueError('Date does not match the confirmed date convention.') from None

def decimal_value(value,convention,places,negative=False):
    value=str(value).strip()
    if value.startswith('(') and value.endswith(')'):value='-'+value[1:-1]
    value=re.sub(r'^(-?)[\$] *',r'\1',value)
    if convention=='comma':
        if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?',value):raise ValueError('Amount does not match decimal-comma formatting.')
        value=value.replace('.','').replace(',','.')
    elif convention=='dot':
        if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?',value):raise ValueError('Amount does not match decimal-point formatting.')
        value=value.replace(',','')
    else:raise ValueError('Confirm the decimal convention.')
    try:
        result=Decimal(value)
        if not result.is_finite() or abs(result)>Decimal('99999999') or (result<0 and not negative) or result.as_tuple().exponent < -places:
            raise ValueError('Amount is outside the supported range or decimal precision.')
        return result
    except InvalidOperation:raise ValueError('Use a valid fixed decimal amount.') from None

def stamp(value,convention):
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})',str(value)):
        return datetime.fromisoformat(str(value).replace('Z','+00:00')).isoformat()
    return day(value,convention)+'T00:00:00+00:00'

def date_only(value):return not bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})',str(value)))

def check_config(table,category,config):
    if config.get('confirmed') is not True:raise TableError('MAPPING_CONFIRMATION','Review and confirm the column and value mappings first.')
    mapping=config.get('mapping',{})
    constants=config.get('constants',{})
    maps=config.get('value_maps',{})
    if not isinstance(maps,dict) or set(maps)-{'role',*VALUES} or any(not isinstance(values,dict) or len(values)>100 for values in maps.values()):
        raise TableError('VALUE_MAPPING_FIELDS','Value mappings may contain only supported roles, statuses and hourly components, with at most 100 source values each.')
    allowed={'facility_id','role','component','currency','approval_state','state','document_kind','contract_id','authorization_date','approval_observed_at','billing_basis'}
    if not isinstance(constants,dict) or set(constants)-allowed or set(constants)&set(mapping) or any(not isinstance(v,str) or not v or len(v)>80 for v in constants.values()):
        raise TableError('FIXED_VALUES','Confirm supported fixed values separately from mapped columns.')
    if not isinstance(mapping,dict) or set(mapping)-set(FIELDS[category]) or any(v not in table['headers'] for v in mapping.values()):
        raise TableError('MAPPING_FIELDS','Mapped columns must exist in this worksheet.')
    scope_column=mapping.get('billing_basis')
    all_non_hourly=category=='invoices' and (constants.get('billing_basis')=='non_hourly' or bool(scope_column) and bool(table['rows']) and all(maps.get('billing_basis',{}).get(row['values'][table['headers'].index(scope_column)])=='non_hourly' for row in table['rows']))
    required=[label for field,(label,needed,_) in FIELDS[category].items() if needed and not (all_non_hourly and field in ['hours','unit_rate']) and not mapping.get(field) and not constants.get(field)]
    if required:raise TableError('REQUIRED_MAPPING','Map required fields: '+', '.join(required))
    if config.get('date_format') not in DATE_FORMATS or config.get('decimal_format') not in ['dot','comma'] or config.get('time_unit') not in ['hours','minutes'] or config.get('end_date_mode') not in ['exclusive','inclusive']:
        raise TableError('FORMAT_CONFIRMATION','Confirm date, decimal, time-unit and end-date conventions.')
    hint=time_unit_hint(mapping.get('hours',''))
    if category!='rates' and not all_non_hourly and hint and hint!=config.get('time_unit'):
        raise TableError('TIME_UNIT_MISMATCH',f'The selected time column is labeled in {hint}. Choose {hint} as the time unit; do not convert it a second time.')
    if category=='invoices' and not all_non_hourly and not mapping.get('shift_ids') and not all(mapping.get(k) or constants.get(k) for k in ['worker_id','service_date','role','component']):
        raise TableError('MATCHING_FIELDS','Map work references, or all four matching fields: worker, service date, role and component.')

def normalize_table(table,category,config,filename,content_hash):
    check_config(table,category,config)
    records=[];errors=[];lineage=[];seen={};duplicates=0
    mapping=config['mapping'];value_maps=config.get('value_maps',{})
    for row in table['rows']:
        raw={**config.get('constants',{}),**{key:row['values'][table['headers'].index(header)] for key,header in mapping.items()}}
        field=''
        try:
            def value(key,default=None):
                nonlocal field
                field=key
                result=raw.get(key,'')
                if result=='':
                    if default is not None:return default
                    raise ValueError('A required value is missing.')
                return result
            def ref(key,default=None):return identifier(value(key,default))
            def date_value(key):return day(value(key),config['date_format'])
            def number(key,places=4,negative=False):return decimal_value(value(key),'dot' if mapping.get(key) in row.get('numeric_columns',[]) else config['decimal_format'],places,negative)
            def mapped(key):
                source=value(key)
                result=source if key in config.get('constants',{}) else value_maps.get(key,{}).get(source)
                if result is None or result=='':raise ValueError('Confirm a value mapping for every source value.')
                if key in VALUES and result not in VALUES[key]:raise ValueError('Choose a supported status or hourly component.')
                if key=='role' and not re.fullmatch(r'[A-Za-z0-9 _-]{1,60}',result):raise ValueError('Use a role label of up to 60 safe characters.')
                return result
            def minutes(credit=False):
                n=abs(number('hours',negative=credit))*(60 if config['time_unit']=='hours' else 1)
                if n!=n.to_integral_value() or n>1000000:raise ValueError('Time must resolve to whole minutes (for example 7.5 hours or 450 minutes). Use the original minutes column for rounded decimal-hour exports; no time is rounded here.')
                return int(n)
            if category=='rates':
                start=date_value('effective_from')
                end=date_value('effective_to') if raw.get('effective_to') else None
                if end and config['end_date_mode']=='inclusive':end=(date.fromisoformat(end)+timedelta(days=1)).isoformat()
                if end and end<=start:field='effective_to';raise ValueError('Effective end must follow the start.')
                record={'id':ref('id'),'contract_id':ref('contract_id'),'facility_id':ref('facility_id'),'role':mapped('role'),'component':mapped('component'),
                        'rate':format(number('rate'),'.4f'),'currency':value('currency','USD').upper(),'effective_from':start,'effective_to':end,
                        'authorization_date':date_value('authorization_date'),'supersedes':ref('supersedes') if raw.get('supersedes') else None}
            elif category=='work':
                approval=mapped('approval_state')
                approved=stamp(value('approved_at'),config['date_format']) if raw.get('approved_at') else None
                # Missing approval evidence stays missing. The engine makes a coverage task.
                record={'id':ref('id'),'facility_id':ref('facility_id'),'worker_id':ref('worker_id'),'assignment_id':ref('assignment_id','UNSPECIFIED'),
                        'role':mapped('role'),'component':mapped('component'),'service_date':date_value('service_date'),
                        'worked_minutes':minutes(),'approval_state':approval,'approved_at':approved,'timezone':'UTC',
                        'recorded_at':date_value('service_date')+'T00:00:00+00:00'}
                if approved:record['approval_date_only']=date_only(raw['approved_at'])
                if raw.get('approval_observed_at'):
                    record['approval_observed_at']=stamp(value('approval_observed_at'),config['date_format'])
                    record['approval_observation_date_only']=date_only(raw['approval_observed_at'])
                if raw.get('service_end_date'):
                    record['service_end_date']=date_value('service_end_date')
                    if record['service_end_date']<record['service_date']:field='service_end_date';raise ValueError('Service end precedes the start.')
                version=value('source_revision',digest(record)[:24])
                if len(version)>80:raise ValueError('Use a source version of at most 80 characters.')
                record['source_revision']=version
            else:
                amount=number('amount',2,True);kind=mapped('document_kind')
                if (kind=='credit' and amount>0) or (kind!='credit' and amount<0):field='amount';raise ValueError('Use signed amounts: credit memos must be negative and invoice/debit amounts nonnegative. Credit amounts are not inferred.')
                basis=mapped('billing_basis') if raw.get('billing_basis') else 'hourly'
                field='shift_ids'
                refs=[identifier(v.strip()) for v in str(raw.get('shift_ids','')).split(';') if v.strip()]
                record={'id':ref('id'),'invoice_id':ref('invoice_id'),'facility_id':ref('facility_id'),'state':mapped('state'),'document_kind':kind,
                        'amount':format(amount,'.2f'),'currency':value('currency','USD').upper(),'minutes':minutes(kind=='credit') if basis=='hourly' else 0,'unit_rate':format(number('unit_rate'),'.4f') if basis=='hourly' else '0.0000',
                        'shift_ids':refs,'chain_id':ref('chain_id') if raw.get('chain_id') else None}
                if basis=='non_hourly':
                    if refs:raise ValueError('A non-hourly line cannot also allocate to hourly work. Confirm its scope and remove work references only if it is outside the hourly agreement.')
                    record['billing_basis']=basis
                if basis=='hourly' and not refs and record['state']=='posted':
                    record['_match']={'worker_id':ref('worker_id'),'service_date':date_value('service_date'),'role':mapped('role'),'component':mapped('component')}
            if record.get('currency','USD')!='USD':field='currency';raise ValueError('This release supports USD only.')
            if category=='invoices':
                native=record['id'];joined=record['invoice_id']+'__'+native
                record['id']=joined if len(joined)<=80 else 'LINE-'+digest(joined)[:24]
            old=seen.get(record['id'])
            if old is not None:
                if old!=record:field='id';raise ValueError('This reference has conflicting rows. Supply distinct IDs or correct the source version.')
                duplicates+=1
            else:
                seen[record['id']]=record;records.append(record)
            lineage.append({'kind':category,'record_id':record['id'],'filename':filename,'worksheet':table['worksheet'],'row':row['row_number'],'sha256':content_hash})
        except (ValueError,OverflowError) as error:
            errors.append({'filename':filename,'worksheet':table['worksheet'],'row':row['row_number'],'field':field,'code':'ROW_VALUE','message':str(error)})
    return {'records':records,'errors':errors,'lineage':lineage,'duplicates':duplicates,'source_rows':len(table['rows'])}

def error_csv(errors):
    output=io.StringIO();writer=csv.writer(output)
    writer.writerow(['File','Worksheet','Row','Field','Code','Correction'])
    for error in errors:
        values=[str(error.get(k,'')) for k in ['filename','worksheet','row','field','code','message']]
        writer.writerow(["'"+v if re.match(r'^[\s\x00-\x1f]*[=+@-]',v) else v for v in values])
    return output.getvalue()
