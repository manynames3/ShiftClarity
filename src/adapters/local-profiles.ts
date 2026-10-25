import {fields,valueChoices,type Kind,type Mapping,type LocalSource} from './local-tables';
export const volatileFixed=new Set(['approval_observed_at','authorization_date','approval_state','state','document_kind','billing_basis']);
import {headerChanges} from '../import-helpers';
export interface LocalProfile {kind:Kind;headers:string[];config:Mapping}
export function profileText(sources:LocalSource[]){return JSON.stringify({format:'shiftclarity-local-mappings-v1',profiles:sources.filter(s=>s.config.confirmed).map(s=>({kind:s.kind,headers:s.table.headers,config:{...s.config,fixed:Object.fromEntries(Object.entries(s.config.fixed).filter(([key])=>!volatileFixed.has(key))),confirmed:false}}))},null,2);}
export function parseProfiles(text:string):LocalProfile[]{
 if(text.length>128*1024)throw Error('Mapping profiles must be under 128 KiB.');
 const pack=JSON.parse(text);if(pack?.format!=='shiftclarity-local-mappings-v1'||!Array.isArray(pack.profiles)||pack.profiles.length>9||Object.keys(pack).some(k=>!['format','profiles'].includes(k)))throw Error('Use a downloaded ShiftClarity mapping-profile file.');
 return pack.profiles.map((p:LocalProfile)=>{
  if(!['work','invoices','rates'].includes(p.kind)||!Array.isArray(p.headers)||!p.headers.length||p.headers.length>50||p.headers.some(h=>typeof h!=='string'||h.length>100)||Object.keys(p).some(k=>!['kind','headers','config'].includes(k)))throw Error('Invalid profile header definition.');
  const c=p.config;if(!c||!['ISO','MDY','DMY'].includes(c.date)||!['dot','comma'].includes(c.decimal)||!['hours','minutes'].includes(c.unit)||!['exclusive','inclusive'].includes(c.end)||Object.keys(c).some(k=>!['columns','fixed','values','date','decimal','unit','end','confirmed'].includes(k)))throw Error('Invalid profile conventions.');
  for(const [key,v] of Object.entries(c.columns||{}))if(!Object.hasOwn(fields[p.kind],key)||typeof v!=='string'||!p.headers.includes(v))throw Error('Profile contains an unknown mapped column.');
  for(const [key,v] of Object.entries(c.fixed||{}))if(!Object.hasOwn(fields[p.kind],key)||typeof v!=='string'||v.length>80||['worker_id','id','invoice_id','shift_ids','approved_at','service_date','hours','unit_rate','amount','rate'].includes(key))throw Error('Profile contains an unsupported fixed value.');
  for(const [field,values] of Object.entries(c.values||{})){if(!Object.hasOwn(fields[p.kind],field)||!['role',...Object.keys(valueChoices)].includes(field)||!values||typeof values!=='object'||Object.keys(values).length>100)throw Error('Invalid profile value mapping.');for(const [key,v] of Object.entries(values))if(key.length>2000||typeof v!=='string'||v.length>80)throw Error('Invalid profile value.');}
  return {kind:p.kind,headers:p.headers,config:{...c,columns:c.columns||{},fixed:Object.fromEntries(Object.entries(c.fixed||{}).filter(([key])=>!volatileFixed.has(key))),values:c.values||{},confirmed:false}};
 });
}
export function applyLocalProfile(source:LocalSource,profiles:LocalProfile[]):Mapping{
 const matches=profiles.filter(p=>p.kind===source.kind&&JSON.stringify(p.headers)===JSON.stringify(source.table.headers));
 if(matches.length!==1){const candidate=profiles.find(p=>p.kind===source.kind);if(candidate){const d=headerChanges(candidate.headers,source.table.headers);throw Error('No unique exact-header profile. Added: '+(d.added.join(', ')||'none')+'. Removed: '+(d.removed.join(', ')||'none')+(d.reordered?'. Columns reordered.':'.')+' Review this mapping explicitly.');}throw Error('No profile for this source category.');}
 const c=structuredClone(matches[0].config),values:Mapping['values']={};
 for(const [field,header] of Object.entries(c.columns)){if(!['role',...Object.keys(valueChoices)].includes(field))continue;const seen=[...new Set(source.table.rows.map(r=>r.values[source.table.headers.indexOf(header)]).filter(Boolean))];if(seen.length>100)throw Error('Too many distinct source codes.');values[field]=Object.fromEntries(seen.map(value=>[value,c.values[field]?.[value]||'']));}
 return {...c,values,confirmed:false};
}
