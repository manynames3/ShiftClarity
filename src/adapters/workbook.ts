import * as XLSX from 'xlsx';
import type {BillingReport} from '../domain/report';
export interface WorkbookSheet {name:string;rows:string[][];numeric?:number[][]}
export interface LocalWorkbook {sheets:WorkbookSheet[]}
const MAX_FILE=2*1024*1024,MAX_XML=16*1024*1024;
const fail=(message:string):never=>{throw Error(message);};
function decodedXml(text:string){return text.replace(/&#(x[\da-f]+|\d+);/gi,(_,code:string)=>String.fromCodePoint(code[0].toLowerCase()==='x'?parseInt(code.slice(1),16):parseInt(code,10))).replaceAll('&quot;','"').replaceAll('&apos;',"'");}
// Validate the ZIP directory and bounded decompressed bytes before the workbook parser sees them.
export async function preflightWorkbook(buffer:ArrayBuffer){
 const data=new Uint8Array(buffer),view=new DataView(buffer);if(!data.length||data.length>MAX_FILE)fail('Choose a nonempty workbook no larger than 2 MiB.');
 let end=-1;for(let i=data.length-22;i>=Math.max(0,data.length-65557);i--)if(view.getUint32(i,true)===0x06054b50&&i+22+view.getUint16(i+20,true)===data.length){end=i;break;}
 if(end<0)fail('Use a valid values-only XLSX workbook. Legacy XLS, encrypted and macro workbooks are not accepted.');
 const count=view.getUint16(end+10,true),size=view.getUint32(end+12,true),offset=view.getUint32(end+16,true);
 if(view.getUint16(end+4,true)||view.getUint16(end+6,true)||count!==view.getUint16(end+8,true)||!count||count>150||offset+size!==end)fail('Workbook archive exceeds supported limits or uses an unsupported ZIP layout.');
 let cursor=offset,total=0,cellCount=0;const names=new Set<string>(),ranges:{start:number;end:number}[]=[];
 for(let i=0;i<count;i++){
  if(cursor+46>end||view.getUint32(cursor,true)!==0x02014b50)fail('Invalid workbook archive directory.');
  const flags=view.getUint16(cursor+8,true),method=view.getUint16(cursor+10,true),compressed=view.getUint32(cursor+20,true),expanded=view.getUint32(cursor+24,true),nameLength=view.getUint16(cursor+28,true),extra=view.getUint16(cursor+30,true),comment=view.getUint16(cursor+32,true),local=view.getUint32(cursor+42,true);
  if(cursor+46+nameLength+extra+comment>end||view.getUint16(cursor+34,true))fail('Invalid workbook entry.');
  const name=new TextDecoder('utf-8',{fatal:true}).decode(data.subarray(cursor+46,cursor+46+nameLength)),lower=name.toLowerCase();cursor+=46+nameLength+extra+comment;
  total+=expanded;
  if(!name||names.has(lower)||name.includes('\0')||name.includes('\\')||name.startsWith('/')||name.split('/').includes('..')||flags&1||![0,8].includes(method)||expanded>MAX_XML||total>MAX_XML||expanded>Math.max(1,compressed)*200)fail('Workbook archive is encrypted, oversized, ambiguous or unsafe. Save a smaller values-only XLSX.');
  names.add(lower);
  if(/vbaproject|externallinks\/|embeddings\/|activex\/|macrosheets\/|connections\.xml|querytables\/|pivotcache/.test(lower)||lower.endsWith('.bin')&&!/^xl\/printersettings\/printersettings\d+\.bin$/.test(lower))fail('Remove macros, embedded objects, connections and external data from the workbook.');
  if(local+30>offset||view.getUint32(local,true)!==0x04034b50||view.getUint16(local+6,true)!==flags||view.getUint16(local+8,true)!==method)fail('Workbook entry metadata is inconsistent.');
  const localNameLength=view.getUint16(local+26,true),localExtra=view.getUint16(local+28,true),start=local+30+localNameLength+localExtra;
  if(start+compressed>offset||new TextDecoder().decode(data.subarray(local+30,local+30+localNameLength))!==name||ranges.some(r=>local<r.end&&start+compressed>r.start))fail('Workbook entry ranges overlap or extend outside the archive.');
  ranges.push({start:local,end:start+compressed});
  let bytes:Uint8Array;
  if(method===0){if(compressed!==expanded)fail('Workbook size metadata is inconsistent.');bytes=data.subarray(start,start+compressed);}
  else {
   let stream:DecompressionStream;try{stream=new DecompressionStream('deflate-raw');}catch{fail('This browser cannot safely validate compressed workbooks. Update it or save the sheet as CSV UTF-8.');}
   const reader=new Blob([data.slice(start,start+compressed)]).stream().pipeThrough(stream!).getReader(),chunks:Uint8Array[]=[];let length=0;
   try{while(true){const value=await reader.read();if(value.done)break;length+=value.value.byteLength;if(length>expanded||length>MAX_XML)fail('Expanded workbook exceeds declared safe size.');chunks.push(value.value);}if(length!==expanded)fail('Expanded workbook size does not match its directory.');}
   finally{await reader.cancel();}
   bytes=new Uint8Array(length);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}
  }
  if(/\.(xml|rels)$/.test(lower)){
   const text=decodedXml(new TextDecoder('utf-8',{fatal:true}).decode(bytes));if(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(text))fail('Workbook XML must use valid UTF-8 text without control characters.');
   if(/<!DOCTYPE|<!ENTITY|\bTargetMode\s*=\s*["']external["']|\bTarget\s*=\s*["'](?:[a-z][a-z0-9+.-]*:|\/\/)|<(?:[\w.-]+:)?Override\b[^>]*macroEnabled/i.test(text))fail('Formula cells, external references and active XML are not accepted. Export values only.');
   if(/^xl\/worksheets\/[^/]+\.xml$/.test(lower)){
    for(const cell of text.matchAll(/<(?:[\w.-]+:)?c\b[^>]*(?:\/>|>[\s\S]*?<\/(?:[\w.-]+:)?c\s*>)/gi)){cellCount++;if(cellCount>100000)fail('Workbook exceeds 100,000 cells.');if(/<(?:[\w.-]+:)?f\b/i.test(cell[0]))fail('Formula cells are not accepted. Export values only.');const coordinate=cell[0].match(/\br\s*=\s*["']([A-Z]+)(\d+)["']/i);if(coordinate&&(Number(coordinate[2])>2520||coordinate[1].toUpperCase().split('').reduce((n,c)=>n*26+c.charCodeAt(0)-64,0)>50))fail('Use up to 2,500 data rows plus a title/header area, and 50 columns.');}
   }
   if(/<(?:[\w.-]+:)?mergeCell\b/i.test(text))fail('Unmerge the exported worksheet cells before importing.');
   if(/\bstate\s*=\s*["'](?:hidden|veryHidden)["']|<(?:[\w.-]+:)?(?:row|col)\b[^>]*\bhidden\s*=\s*["'](?:true|1)["']/i.test(text))fail('Remove hidden sheets, rows and columns from the exported workbook.');
  }
 }
 if(cursor!==end||!names.has('[content_types].xml')||!names.has('xl/workbook.xml'))fail('Use an XLSX workbook, not a renamed archive or another spreadsheet format.');
 if([...names].filter(n=>/^xl\/worksheets\/[^/]+\.xml$/.test(n)).length>8)fail('Use at most eight worksheets per workbook.');
}
export async function parseWorkbook(buffer:ArrayBuffer):Promise<LocalWorkbook>{
 await preflightWorkbook(buffer);
 const book=XLSX.read(buffer,{type:'array',cellDates:false,cellNF:true,cellHTML:false,cellText:false,cellFormula:true,cellStyles:true,bookVBA:true,nodim:true,WTF:true});
 if(!book.SheetNames.length||book.SheetNames.length>8||book.vbaraw)fail('Use 1–8 visible, values-only worksheets.');
 if(book.Workbook?.Sheets?.some(s=>s.Hidden))fail('Remove hidden worksheets before importing.');
 if(book.Workbook?.Names?.some(n=>/\[/.test(n.Ref||'')||/[()]|https?:/i.test((n.Ref||'').replace(/^'(?:[^']|'')*'!/,''))))fail('Remove calculated or external named references before importing.');
 let cells=0,characters=0;
 return {sheets:book.SheetNames.map(name=>{
  const sheet=book.Sheets[name];if(sheet['!merges']?.length)fail('Unmerge worksheet cells before importing.');
  if(sheet['!rows']?.some(row=>row?.hidden)||sheet['!cols']?.some(col=>col?.hidden))fail('Remove hidden rows and columns before importing.');
  const addresses=Object.keys(sheet).filter(key=>/^[A-Z]+[1-9]\d*$/i.test(key));if(!addresses.length)return {name,rows:[],numeric:[]};
  const range={e:addresses.reduce((end,address)=>{const p=XLSX.utils.decode_cell(address);return {r:Math.max(end.r,p.r),c:Math.max(end.c,p.c)};},{r:0,c:0})};
  if(range.e.r>=2520||range.e.c>=50)fail('Use up to 2,500 data rows plus a header/title area, and 50 columns per worksheet.');
  cells+=(range.e.r+1)*(range.e.c+1);if(cells>100000)fail('Workbook exceeds 100,000 cells.');
  const rows:string[][]=[],numeric:number[][]=[];
  for(let row=0;row<=range.e.r;row++){const values:string[]=[],numericColumns:number[]=[];for(let col=0;col<=range.e.c;col++){
   const cell=sheet[XLSX.utils.encode_cell({r:row,c:col})];let value='';
   if(cell){if(cell.f||cell.F||cell.l||cell.c?.length||cell.t==='e')fail('Remove formulas, links, comments and error cells. Export values only.');
    if(cell.t==='n'&&cell.z&&XLSX.SSF.is_date(cell.z)){
     const date=XLSX.SSF.parse_date_code(cell.v,{date1904:book.Workbook?.WBProps?.date1904});if(!date)fail('Invalid Excel date cell.');
     value=`${date.y}-${String(date.m).padStart(2,'0')}-${String(date.d).padStart(2,'0')}`;
     if(new Date(value).toISOString().slice(0,10)!==value)fail('Invalid Excel calendar date.');
    }else {if(typeof cell.v==='number'&&!Number.isFinite(cell.v))fail('Non-finite workbook number.');value=cell.v===undefined?'':String(cell.v);if(cell.t==='n')numericColumns.push(col);}
   }
   if(value.length>2000||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value))fail('A workbook cell exceeds the safe text limits.');characters+=value.length;if(characters>2*1024*1024)fail('Workbook exceeds 2 MiB of expanded cell text.');values.push(value);
  }rows.push(values);numeric.push(numericColumns);}
  return {name,rows,numeric};
 })};
}
export function reportWorkbook(report:BillingReport):ArrayBuffer{
 const book=XLSX.utils.book_new();book.Props={Title:'ShiftClarity billing review',Author:'ShiftClarity',Subject:report.synthetic?'Fictional evaluation':'User-supplied local evaluation'};
 for(const table of report.tables){const sheet=XLSX.utils.aoa_to_sheet([table.headers,...table.rows]);if(sheet['!ref'])sheet['!autofilter']={ref:sheet['!ref']};sheet['!cols']=table.headers.map((h,i)=>({wch:i===0?32:/reference|source|reason|basis|limit/i.test(h)?45:24}));
  for(const [address,cell] of Object.entries(sheet)){if(address.startsWith('!'))continue;if(cell.t==='s'){delete cell.f;delete cell.l;}if(cell.t==='n'&&/USD|amount|difference/i.test(table.headers[XLSX.utils.decode_cell(address).c]))cell.z=/rate/i.test(table.headers[XLSX.utils.decode_cell(address).c])?'#,##0.0000':'#,##0.00;[Red](#,##0.00)';}
  XLSX.utils.book_append_sheet(book,sheet,table.name.slice(0,31));
 }
 return XLSX.write(book,{type:'array',bookType:'xlsx',compression:true});
}
