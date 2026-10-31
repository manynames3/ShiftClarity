import {dateValue,fields,parseCsv,token,type Kind,type LocalSource,type LocalTable} from './local-tables';

// Suggestions never confirm mappings, completeness, units or approval authority.
export function inspectSource(source:LocalSource){
 const {kind,table,config}=source,headers=table.headers.map(token);
 const missing=Object.entries(fields[kind]).filter(([key,[,required]])=>required&&!config.columns[key]&&!config.fixed[key]).map(([, [label]])=>label);
 const unresolved=Object.entries(config.values).flatMap(([field,values])=>Object.entries(values).filter(([,meaning])=>!meaning).map(([value])=>`${fields[kind][field]?.[0]||field}: ${value}`));
 const weekly=kind==='work'&&!config.columns.service_date&&headers.some(h=>['wedate','weekending','weekworked'].includes(h));
 const recipe=headers.includes('billtransactiondate')?'Bullhorn transaction-detail structure':headers.includes('wedate')&&headers.includes('transtype')?'Avionté weekly-report structure':'Generic spreadsheet';
 return {recipe,missing,unresolved,weekly,status:weekly?'Insufficient detail':missing.length||unresolved.length?'Needs clarification':config.confirmed?'Confirmed':'Ready to confirm'};
}
export function suggestPeriod(sources:LocalSource[]){
 const dates:string[]=[];
 for(const s of sources.filter(s=>s.kind==='work')){const i=s.table.headers.indexOf(s.config.columns.service_date);if(i<0)continue;for(const row of s.table.rows){try{dates.push(dateValue(row.values[i],s.config.date));}catch{return null;}}}
 dates.sort();return dates.length?{from:dates[0],to:dates.at(-1)!}:null;
}
export function readSuggestedCsv(name:string,text:string,hash:string,kind:Kind,preferred=1):LocalTable{
 // Try bounded header candidates; only suggest a later header if it has more recognized fields.
 const candidates:{table:LocalTable;score:number;row:number}[]=[];let original:unknown;
 for(let row=1;row<=20;row++){try{const table=parseCsv(name,text,hash,row),score=table.headers.filter(h=>Object.entries(fields[kind]).some(([key,[,,aliases]])=>[key,...aliases].map(token).includes(token(h)))).length;candidates.push({table,score,row});if(score>=3&&row>=preferred)break;}catch(e){if((e as Error).message.startsWith('Remove personal or clinical columns'))throw e;if(row===preferred)original=e;}}
 const selected=candidates.find(c=>c.row===preferred);
 if(preferred>1){if(selected)return selected.table;throw original||Error('Choose the row containing column names.');}
 const best=candidates.sort((a,b)=>b.score-a.score)[0];
 if(best&&best.score>=3&&(!selected||best.score>selected.score))return best.table;
 if(selected)return selected.table;
 throw original||Error('Choose the row containing unique column names, then export a fresh UTF-8 CSV.');
}
export function localToUtc(value:string,zone:string){
 if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value))throw Error('Enter a complete reporting date and time.');
 const target=Date.parse(value+':00Z');if(!Number.isFinite(target)||new Date(target).toISOString().slice(0,16)!==value)throw Error('Enter a real reporting date and time.');
 const fmt=new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
 const render=(stamp:number)=>{const parts=Object.fromEntries(fmt.formatToParts(stamp).map(p=>[p.type,p.value]));return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;};
 const offsets=new Set<number>();for(const shift of [-36,0,36]){const stamp=target+shift*3600000;offsets.add(Date.parse(render(stamp)+':00Z')-stamp);}
 const matches=[...offsets].map(offset=>target-offset).filter(stamp=>render(stamp)===value);
 if(matches.length!==1)throw Error('This local time is missing or repeated during a daylight-saving change. Choose UTC and enter the exact source timestamp.');
 return new Date(matches[0]).toISOString();
}
