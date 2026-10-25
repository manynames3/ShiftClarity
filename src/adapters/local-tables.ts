import Decimal from 'decimal.js';
import schema from './table-schema.json';
import type {Inputs,Work,Invoice,Rule,Batch} from '../domain/types';
import {parseCustom} from './custom';
export type Kind='work'|'invoices'|'rates';
export interface LocalTable {name:string;headers:string[];rows:{number:number;values:string[]}[];sha256:string;numeric?:Record<number,string[]>;skipped_rows?:number}
export interface Mapping {columns:Record<string,string>;fixed:Record<string,string>;values:Record<string,Record<string,string>>;date:'ISO'|'MDY'|'DMY';decimal:'dot'|'comma';unit:'hours'|'minutes';end:'exclusive'|'inclusive';confirmed:boolean}
export interface LocalSource {kind:Kind;table:LocalTable;config:Mapping}
export interface LocalPeriod {from:string;to:string;asOf:string;cutoff:string;workComplete:boolean;invoiceComplete:boolean;workHours:string;invoiceTotal:string;author:string;approver:string}
export const fields=schema.fields as unknown as Record<Kind,Record<string,[string,boolean,string[]]>>;
export const valueChoices=schema.values as Record<string,Record<string,string[]>>;
export const token=(v:string)=>v.toLowerCase().replace(/[^a-z0-9]/g,'');
const id=(v:string)=>{if(!/^[A-Za-z0-9_-]{1,80}$/.test(v))throw Error('Use a stable ID: up to 80 letters, numbers, underscores or hyphens. Names are not reference IDs.');return v;};
export function dateValue(v:string,mode:Mapping['date']){
 let y:string,m:string,d:string;
 if(/^\d{4}-\d{2}-\d{2}$/.test(v))[y,m,d]=v.split('-');
 else {const parts=v.split('/');if(parts.length!==3||mode==='ISO')throw Error('Date must match the confirmed date convention.');[m,d,y]=mode==='MDY'?parts:[parts[1],parts[0],parts[2]];}
 const out=`${y}-${m.padStart(2,'0')}-${d.padStart(2,'0')}`;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(out)||Number.isNaN(Date.parse(out))||new Date(out).toISOString().slice(0,10)!==out)throw Error('Use a real calendar date in the confirmed format.');return out;
}
export function decimalValue(v:string,mode:Mapping['decimal'],places:number,negative=false){
 v=v.trim().replace(/^\((.*)\)$/,'-$1').replace(/^(-?)\$\s*/,'$1');
 const pattern=mode==='dot'?/^-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?$/:/^-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?$/;
 if(!pattern.test(v))throw Error('Amount does not match the confirmed decimal convention.');
 const clean=mode==='dot'?v.replaceAll(',',''):v.replaceAll('.','').replace(',','.');const n=new Decimal(clean);
 if(n.abs().gt(99999999)||!negative&&n.isNegative()||(clean.split('.')[1]?.length||0)>places)throw Error('Amount exceeds the supported range or precision. No rounding is applied on import.');return n;
}
export function tableFromRows(name:string,raw:string[][],sha256=''):LocalTable{
 if(!raw.length||raw.length>2501)throw Error('Use a header and up to 2,500 data rows per file.');
 const headers=raw[0].map(v=>v.trim());
 if(!headers.length||headers.length>50||headers.some(h=>!h||h.length>100)||new Set(headers.map(token)).size!==headers.length)throw Error('Use 1–50 unique, nonempty column headers, up to 100 characters each.');
 const denied=headers.filter(h=>schema.denied.includes(token(h))||/^(patient|diagnosis|clinical|medicalrecord)/.test(token(h)));
 if(denied.length)throw Error('Remove personal or clinical columns before testing: '+denied.slice(0,8).join(', ')+'. Export stable worker IDs instead of names.');
 const rows=raw.slice(1).map((values,i)=>({number:i+2,values:values.map(v=>v.trim())}));
 if(rows.some(r=>r.values.length!==headers.length||r.values.some(v=>v.length>2000)))throw Error('Each row must have the same number of columns as the header; cells may contain up to 2,000 characters.');
 if(!rows.length)throw Error('This file has no data rows. For a genuinely empty invoice export, use the explicit zero-total declaration.');
 return {name,headers,rows,sha256};
}
export function parseCsv(name:string,text:string,sha256='',headerRow=1):LocalTable{
 if(!Number.isInteger(headerRow)||headerRow<1||headerRow>20)throw Error('Choose a header row from 1 to 20.');
 if(new TextEncoder().encode(text).length>2*1024*1024)throw Error('Use files no larger than 2 MiB. Split large exports by facility and period.');
 text=text.replace(/^\uFEFF/,'');if(text.includes('\0'))throw Error('Use UTF-8 CSV text; binary files and UTF-16 exports must be saved as UTF-8 first.');
 // Delimiters inside quoted fields are excluded from detection.
 let quoted=false,first='',scanLine=1;for(let i=0;i<text.length;i++){const c=text[i];if(c==='\n'||c==='\r'){if(!quoted&&scanLine===headerRow)break;if(c==='\r'&&text[i+1]==='\n')i++;scanLine++;continue;}if(c==='"')quoted=!quoted;if(!quoted&&scanLine===headerRow)first+=c;}
 const delimiter=[',',';','\t','|'].sort((a,b)=>first.split(b).length-first.split(a).length)[0];
 const out:string[][]=[],rowNumbers:number[]=[];let row:string[]=[],cell='',inQuote=false,closed=false,lineNumber=1,rowStart=1;
 function pushCell(){row.push(cell);cell='';closed=false;if(row.length>50)throw Error('Use up to 50 columns.');}
 function pushRow(){pushCell();if(row.some(v=>v!=='')){out.push(row);rowNumbers.push(rowStart);}row=[];if(out.length>2520)throw Error('Use up to 2,500 data rows per file.');}
 for(let i=0;i<text.length;i++){
  const c=text[i];if(inQuote){if(c==='"'){if(text[i+1]==='"'){cell+='"';i++;}else{inQuote=false;closed=true;}}else {cell+=c;if(c==='\n')lineNumber++;else if(c==='\r'&&text[i+1]!=='\n')lineNumber++;}}
  else if(c==='"'){if(cell||closed)throw Error('Malformed CSV quoting. Export a fresh CSV from the source.');inQuote=true;}
  else if(c===delimiter)pushCell();else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;pushRow();lineNumber++;rowStart=lineNumber;}
  else {if(closed)throw Error('Unexpected text after a quoted CSV field.');cell+=c;}
  if(cell.length>2000)throw Error('A cell exceeds 2,000 characters. Remove notes and descriptions.');
 }
 if(inQuote)throw Error('CSV contains an unclosed quoted field.');if(cell||row.length||closed)pushRow();const headerIndex=rowNumbers.indexOf(headerRow);if(headerIndex<0)throw Error('The selected header row is blank or inside a quoted field. Choose the row containing column names.');const table=tableFromRows(name,out.slice(headerIndex),sha256);table.skipped_rows=headerIndex;table.rows.forEach((r,i)=>r.number=rowNumbers[headerIndex+i+1]);return table;
}
export function suggestMapping(table:LocalTable,kind:Kind):Mapping{
 const columns:Record<string,string>={};for(const [field,[,,aliases]] of Object.entries(fields[kind])){const matches=table.headers.filter(h=>[field,...aliases].map(token).includes(token(h)));if(matches.length===1)columns[field]=matches[0];}
 const config:Mapping={columns,fixed:{},values:{},date:'ISO',decimal:'dot',unit:'hours',end:'exclusive',confirmed:false};
 if(/minute|mins$/.test(token(columns.hours||'')))config.unit='minutes';return refreshValues(table,config);
}
export function refreshValues(table:LocalTable,config:Mapping):Mapping{
 const values:Mapping['values']={};for(const field of ['role',...Object.keys(valueChoices)]){const header=config.columns[field];if(!header)continue;const distinct=[...new Set(table.rows.map(r=>r.values[table.headers.indexOf(header)]).filter(Boolean))].sort();if(distinct.length>100)throw Error('Use up to 100 distinct values per mapped role, status or component.');values[field]=Object.create(null);for(const source of distinct)values[field][source]=config.values[field]?.[source]??(field==='role'?source:Object.entries(valueChoices[field]).find(([key,aliases])=>[key,...aliases].map(token).includes(token(source)))?.[0]||'');}
 return {...config,values,confirmed:false};
}
export interface RowIssue {file:string;row:number;field:string;message:string}
export class LocalImportError extends Error {constructor(public issues:RowIssue[]){super(`${issues.length} correction(s) required. ${issues[0].file}, row ${issues[0].row}, ${issues[0].field}: ${issues[0].message}`);}}
export function buildLocalBundle(sources:LocalSource[],period:LocalPeriod):{inputs:Inputs;warnings:string[]}{
 const approvalStamp=(value:string,convention:Mapping['date'])=>{if(/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value)){if(Number.isNaN(Date.parse(value)))throw Error('Invalid approval timestamp.');return {at:new Date(value).toISOString(),dateOnly:false};}return {at:dateValue(value,convention)+'T00:00:00Z',dateOnly:true};};
 const from=dateValue(period.from,'ISO'),last=dateValue(period.to,'ISO'),end=new Date(Date.parse(last)+86400000).toISOString().slice(0,10);
 if(last<from||Date.parse(end)-Date.parse(from)>93*86400000)throw Error('Choose a service period of 1–93 days.');
 if(!sources.some(s=>s.kind==='rates')||!sources.some(s=>s.kind==='work'))throw Error('Supply work records and approved rate terms.');
 if(!sources.some(s=>s.kind==='invoices')&&!(period.invoiceComplete&&period.invoiceTotal!==''&&decimalValue(period.invoiceTotal,'dot',2,true).isZero()))throw Error('Supply invoice lines, or explicitly declare a complete empty export and an independent posted total of zero.');
 for(const t of [period.asOf,period.cutoff])if(!/(Z|[+-]\d{2}:\d{2})$/.test(t)||Number.isNaN(Date.parse(t)))throw Error('Source current-through and billing cutoff require explicit UTC or offset timestamps.');
 if(Date.parse(period.cutoff)<Date.parse(end+'T00:00:00Z'))throw Error('Choose a billing cutoff after the selected service period ends. Use a closed period.');
 if(Date.parse(period.cutoff)>Date.parse(period.asOf)&&period.invoiceComplete)throw Error('A complete invoice export must be current through the billing cutoff.');
 id(period.author);id(period.approver);if(period.author===period.approver)throw Error('Supply distinct rate-author and independent-approver references. These declarations are not authenticated.');
 const work:Work[]=[],invoices:Invoice[]=[],rules:Rule[]=[],batches:Batch[]=[],excerpts:Inputs['excerpts']=[],issues:RowIssue[]=[],warnings:string[]=[];
 const invoiceMatches=new Map<Invoice,Record<string,string>>();let duplicates=0;
 sources.forEach((source,sourceIndex)=>{
  const {kind,table,config:c}=source;if(table.skipped_rows)warnings.push(`${table.name}: ${table.skipped_rows} nonblank row(s) above the selected header were excluded. Verify they are report titles/notes, not service or billing records.`);const batch=`LOCAL-BATCH-${sourceIndex+1}`,records:(Work|Invoice|Rule)[]=[];
  if(!c.confirmed)throw Error(`${table.name}: confirm columns, values and conventions first.`);
  const hint=/minute|mins$/.test(token(c.columns.hours||''))?'minutes':/hour|hrs$/.test(token(c.columns.hours||''))?'hours':'';
  const allNonHourlyHint=kind==='invoices'&&table.rows.every(row=>(c.fixed.billing_basis||c.values.billing_basis?.[row.values[table.headers.indexOf(c.columns.billing_basis)]])==='non_hourly');
  if(!allNonHourlyHint&&hint&&hint!==c.unit)throw Error(`${table.name}: selected time column is labeled in ${hint}; confirm ${hint} to prevent a second conversion.`);
  const allNonHourly=kind==='invoices'&&table.rows.every(row=>(c.fixed.billing_basis||c.values.billing_basis?.[row.values[table.headers.indexOf(c.columns.billing_basis)]])==='non_hourly');
  const missing=Object.entries(fields[kind]).filter(([k,[,required]])=>required&&!(allNonHourly&&['hours','unit_rate'].includes(k))&&!c.columns[k]&&!c.fixed[k]).map(([, [label]])=>label);
  if(missing.length)throw Error(`${table.name}: map ${missing.join(', ')}. Weekly totals, assignment start dates and payment dates cannot replace dated service records.`);
  for(const row of table.rows){let field='';try{
   const get=(key:string,fallback?:string)=>{field=key;const value=c.fixed[key]??row.values[table.headers.indexOf(c.columns[key])];if(value===undefined||value===''){if(fallback!==undefined)return fallback;throw Error('Required value is missing.');}return value;};
   const ref=(key:string,fallback?:string)=>id(get(key,fallback));
   const day=(key:string)=>dateValue(get(key),c.date);
   const mapped=(key:string)=>{const v=get(key);const out=c.fixed[key]??c.values[key]?.[v];if(!out)throw Error('Confirm a value mapping for every source value.');if(valueChoices[key]&&!Object.hasOwn(valueChoices[key],out))throw Error('Choose a supported status or hourly component.');if(key==='role'&&!/^[A-Za-z0-9 _-]{1,60}$/.test(out))throw Error('Use a role label of up to 60 safe characters.');return out;};
   const number=(key:string,places=4,negative=false)=>decimalValue(get(key),table.numeric?.[row.number]?.includes(c.columns[key])?'dot':c.decimal,places,negative);
   const minutes=(credit=false)=>{const n=number('hours',4,credit).abs().mul(c.unit==='hours'?60:1);if(!n.isInteger()||n.gt(1000000))throw Error('Time must resolve to whole minutes. Use original minutes for rounded decimal-hour exports; time is never rounded here.');return n.toNumber();};
   if(kind==='work'){
    const service=day('service_date');if(service<from||service>=end)throw Error('Service date falls outside the selected period; re-export that scope.');
    const approved=get('approved_at',''),observed=get('approval_observed_at','');
    const w:Work={id:ref('id'),source_revision:get('source_revision',table.sha256||'local-file'),facility_id:ref('facility_id'),worker_id:ref('worker_id'),assignment_id:ref('assignment_id','UNSPECIFIED'),role:mapped('role'),component:mapped('component'),service_date:service,timezone:'UTC',worked_minutes:minutes(),approval_state:mapped('approval_state'),recorded_at:period.asOf,approved_at:approved?approvalStamp(approved,c.date).at:null,...(approved?{approval_date_only:approvalStamp(approved,c.date).dateOnly}:{}),batch_id:batch};
    if(observed){const stamp=approvalStamp(observed,c.date);w.approval_observed_at=stamp.at;w.approval_observation_date_only=stamp.dateOnly;if(Date.parse(stamp.at)>Date.parse(period.asOf)||stamp.at.slice(0,10)<service)throw Error('Approved-status observation must be between service date and files-current timestamp.');}
    if(get('service_end_date','')){w.service_end_date=day('service_end_date');if(w.service_end_date<service)throw Error('Service end precedes start.');}
    if(w.approved_at&&(Date.parse(w.approved_at)>Date.parse(period.asOf)||w.approved_at.slice(0,10)<service))throw Error('Approval date must be between the service date and source current-through.');
    records.push(w);
   }else if(kind==='rates'){
    const start=day('effective_from'),rawEnd=get('effective_to',''),authorized=day('authorization_date');let finish=rawEnd?dateValue(rawEnd,c.date):null;
    if(finish&&c.end==='inclusive')finish=new Date(Date.parse(finish)+86400000).toISOString().slice(0,10);if(finish&&finish<=start)throw Error('Effective end must follow start.');
    if(Date.parse(authorized)>Date.parse(period.asOf))throw Error('Source authorization cannot be after the source current-through.');
    const rid=ref('id'),excerpt='LOCAL-EX-'+sourceIndex+'-'+row.number;
    records.push({id:rid,contract_id:ref('contract_id'),facility_id:ref('facility_id'),role:mapped('role'),component:mapped('component'),rate:number('rate').toFixed(4),currency:get('currency','USD').toUpperCase(),effective_from:start,effective_to:finish,authorization_date:authorized,state:'approved',source_excerpt_id:excerpt,author_id:period.author,approver_id:period.approver,approved_at:authorized+'T00:00:00Z',recorded_at:period.asOf,supersedes:get('supersedes','')?ref('supersedes'):null});
    excerpts.push({id:excerpt,document_id:'LOCAL-DOC-'+sourceIndex,title:'Supplied rate-register row',lines:[`${table.name} · row ${row.number} · SHA-256 ${table.sha256||'unavailable'}. Supplied source approval declaration; verify against the controlling agreement.`],synthetic:false});
   }else{
    const basis=get('billing_basis','')?mapped('billing_basis'):'hourly',kindValue=mapped('document_kind'),amount=number('amount',2,true);
    if(kindValue==='credit'?amount.gt(0):amount.lt(0))throw Error('Credit memos must be signed negative; invoice/debit lines must be nonnegative.');
    const invoiceId=ref('invoice_id'),native=ref('id'),joined=invoiceId+'__'+native;
    if(joined.length>80)throw Error('Combined invoice and line references must fit 80 characters.');
    const refs=get('shift_ids','').split(';').map(v=>v.trim()).filter(Boolean).map(id);
    if(basis==='non_hourly'&&refs.length)throw Error('An outside-hourly-scope line cannot allocate to work references. Confirm its classification.');
    const line:Invoice={id:joined,invoice_id:invoiceId,facility_id:ref('facility_id'),state:mapped('state'),document_kind:kindValue,amount:amount.toFixed(2),currency:get('currency','USD').toUpperCase(),minutes:basis==='hourly'?minutes(kindValue==='credit'):0,unit_rate:basis==='hourly'?number('unit_rate').toFixed(4):'0.0000',shift_ids:refs,chain_id:get('chain_id','')?ref('chain_id'):null,batch_id:batch,...(basis==='non_hourly'?{billing_basis:'non_hourly' as const}:{})};
    if(basis==='hourly'&&!refs.length&&line.state==='posted')invoiceMatches.set(line,Object.fromEntries(['worker_id','service_date','role','component'].map(key=>[key,key==='service_date'?day(key):key==='role'||key==='component'?mapped(key):ref(key)])));
    records.push(line);
   }
   const record=records.at(-1)!;if('currency' in record&&record.currency!=='USD')throw Error('Only USD is supported.');
  }catch(e){issues.push({file:table.name,row:row.number,field,message:(e as Error).message});}}
  const seen=new Map<string,Work|Invoice|Rule>();for(const record of records){const old=seen.get(record.id);if(old){if(JSON.stringify(kind==='rates'?{...old,source_excerpt_id:undefined}:old)!==JSON.stringify(kind==='rates'?{...record,source_excerpt_id:undefined}:record))issues.push({file:table.name,row:0,field:'id',message:'Conflicting repeated reference; supply unique transaction IDs.'});else duplicates++;}else seen.set(record.id,record);}
  const unique=[...seen.values()];if(kind==='work')work.push(...unique as Work[]);if(kind==='invoices')invoices.push(...unique as Invoice[]);if(kind==='rates')rules.push(...unique as Rule[]);
  const ws=unique as Work[],ls=unique as Invoice[];
  batches.push({id:batch,source:(kind==='invoices'?'invoice':kind)+' export · '+table.name+' · SHA-256 '+(table.sha256||'unavailable'),records:unique.length,state:'validated',source_as_of:period.asOf,service_from:from,service_to_exclusive:end,declared_complete:kind==='invoices'?period.invoiceComplete:kind==='work'?period.workComplete:true,...(kind==='work'?{control_total_minutes:ws.reduce((s,w)=>s+w.worked_minutes,0)}:{}),...(kind==='invoices'?{signed_control_total:ls.filter(l=>l.state==='posted').reduce((s,l)=>s.plus(l.amount),new Decimal(0)).toFixed(2)}:{})});
 });
 if(issues.length)throw new LocalImportError(issues);
 for(const rows of [work,invoices,rules])if(new Set(rows.map(r=>r.id)).size!==rows.length)throw Error('References repeat across files. Remove the overlapping export or supply unique transaction references.');
 if(work.length>1000||invoices.length>2000||rules.length>150)throw Error('Use at most 1,000 work records, 2,000 invoice lines and 150 rate versions per review. Split larger exports by period and facility.');
 for(const [line,match] of invoiceMatches){const candidates=work.filter(w=>w.facility_id===line.facility_id&&Object.entries(match).every(([key,v])=>w[key as keyof Work]===v));line.shift_ids=candidates.length===1?[candidates[0].id]:[];}
 const hours=new Decimal(work.reduce((s,w)=>s+w.worked_minutes,0)).div(60),total=invoices.filter(l=>l.state==='posted').reduce((s,l)=>s.plus(l.amount),new Decimal(0));
 if(period.workHours!==''&&!decimalValue(period.workHours,'dot',4).eq(hours))throw Error('Independent work-hour total does not match parsed work. Check filters, units and duplicate exports.');
 if(period.invoiceTotal!==''&&!decimalValue(period.invoiceTotal,'dot',2,true).eq(total))throw Error('Independent signed posted-invoice total does not match parsed lines, including non-hourly charges.');
 if(!invoices.length)batches.push({id:'LOCAL-EMPTY-INVOICE',source:'invoice export · explicitly declared empty',records:0,state:'validated',source_as_of:period.asOf,service_from:from,service_to_exclusive:end,declared_complete:period.invoiceComplete,signed_control_total:'0.00'});
 if(duplicates)warnings.push(`${duplicates} identical repeated record(s) within a file were included once. Check source totals.`);
 if(work.some(w=>w.worked_minutes>1440))warnings.push('Some work rows exceed 24 hours. Verify units and record granularity. Weekly summaries must not stand in for dated shifts.');
 if(work.some(w=>w.approval_observed_at&&!w.approved_at))warnings.push('Approved status was explicitly observed; the original approval-event date is unknown.');
 const fees=invoices.filter(l=>l.billing_basis==='non_hourly');if(fees.length)warnings.push(`${fees.length} explicitly classified non-hourly line(s) are retained in invoice totals, outside hourly comparison. No difference is estimated for them.`);
 if(!period.workComplete||!period.invoiceComplete)warnings.push('Coverage is incomplete. The engine will leave affected work without a financial estimate.');
 const unresolved=invoices.filter(l=>l.state==='posted'&&l.billing_basis!=='non_hourly'&&(!l.shift_ids.length||l.shift_ids.some(ref=>!work.some(w=>w.id===ref))));if(unresolved.length)warnings.push(`${unresolved.length} posted hourly line(s) lack unique work references. Affected facilities remain evidence gaps until the references or matching fields are corrected.`);
 const inputs:Inputs={work,invoices,rules,batches,excerpts,manifest:{dataset_id:'LOCAL-'+from+'-'+last,synthetic:false,version:'local-tables-v1',run_id:'RUN-LOCAL-'+from+'-'+last,as_of:period.asOf,timezone:'UTC',currency:'USD',service_from:from,service_to_exclusive:end,billing_cutoff:period.cutoff,invoice_source_as_of:period.asOf,invoice_coverage_complete:period.invoiceComplete,workspace_label:'Your records · Local evaluation',note:'Supplied exports and approval declarations. Authority, completeness and payment are not independently verified. No upload.'}};
 return {inputs:parseCustom(JSON.stringify(inputs),{bytes:8*1024*1024,rows:2500}),warnings};
}
