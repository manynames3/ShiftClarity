import {execFileSync} from 'node:child_process';
import {Blob as NodeBlob} from 'node:buffer';
import {DecompressionStream as NodeDecompressionStream} from 'node:stream/web';
import {it,expect,vi} from 'vitest';
import * as XLSX from 'xlsx';
import {parseWorkbook,preflightWorkbook,reportWorkbook} from './workbook';
import {workbookTable} from './workbook-table';
import {initialDemo,decide} from '../domain/demo';
import {billingReport} from '../domain/report';
import {freshInputs,draftRule} from './fixtures';
vi.stubGlobal('Blob',NodeBlob);vi.stubGlobal('DecompressionStream',NodeDecompressionStream);
function bytes(change?:(book:XLSX.WorkBook,sheet:XLSX.WorkSheet)=>void,compression=true){const book=XLSX.utils.book_new(),sheet=XLSX.utils.aoa_to_sheet([['Work ID','Service Date','Minutes'],['W1',46300,450]]);sheet.B2.z='yyyy-mm-dd';XLSX.utils.book_append_sheet(book,sheet,'Time');change?.(book,sheet);return XLSX.write(book,{type:'array',bookType:'xlsx',compression}) as ArrayBuffer;}
it('uses the pinned modern package and reads numeric minutes and Excel calendar dates exactly',async()=>{expect(XLSX.version).toBe('0.20.3');for(const compressed of [false,true]){const book=await parseWorkbook(bytes(undefined,compressed));expect(book.sheets[0].rows[1]).toEqual(['W1','2026-10-05','450']);const table=workbookTable('time.xlsx',book.sheets[0],1,'a'.repeat(64));expect(table.rows[0].number).toBe(2);}});
it('requires explicit sheet/header scope and retains original physical row numbers',()=>{const sheet={name:'Time',rows:[['Fictional report','',''],['','',''],['ID','Hours','Status'],['A','8','Yes'],['','',''],['B','7','Yes']]};expect(workbookTable('x.xlsx',sheet,3,'sha').rows.map(r=>r.number)).toEqual([4,6]);expect(()=>workbookTable('x.xlsx',sheet,1,'sha')).toThrow('outside');});
it.each([
 ['formula',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s.C2={t:'n',v:8,f:'2+6'};},/Formula/],
 ['external hyperlink',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s.A2.l={Target:'https://example.invalid/'};},/external/],
 ['hidden row',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s['!rows']=[{}, {hidden:true}];},/hidden/],
 ['hidden column',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s['!cols']=[{hidden:true}];},/hidden/],
 ['hidden sheet',(b:XLSX.WorkBook)=>{XLSX.utils.book_append_sheet(b,XLSX.utils.aoa_to_sheet([['Hidden']]),'Other');b.Workbook={Sheets:[{name:'Time',Hidden:0},{name:'Other',Hidden:1}]};},/hidden/],
 ['merged cells',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s['!merges']=[{s:{r:0,c:0},e:{r:0,c:1}}];},/Unmerge/],
 ['error cells',(_b:XLSX.WorkBook,s:XLSX.WorkSheet)=>{s.C2={t:'e',v:7};},/error/],
] as const)('rejects %s before any evaluation',async(_name,change,pattern)=>{await expect(parseWorkbook(bytes(change))).rejects.toThrow(pattern);});
it('rejects malformed, oversized, overexpanded and excessive-grid workbooks',async()=>{
 await expect(preflightWorkbook(new Uint8Array(30).buffer)).rejects.toThrow('valid');await expect(preflightWorkbook(new Uint8Array(2*1024*1024+1).buffer)).rejects.toThrow('2 MiB');
 const bomb=bytes(),v=new DataView(bomb);for(let i=0;i<bomb.byteLength-46;i++)if(v.getUint32(i,true)===0x02014b50){v.setUint32(i+24,17*1024*1024,true);break;}await expect(preflightWorkbook(bomb)).rejects.toThrow('oversized');
 await expect(parseWorkbook(bytes((_b,s)=>{s['!ref']='A1:AY2';s.AY2={t:'n',v:1};}))).rejects.toThrow('50 columns');
});
it('exports a real multi-sheet workbook with literal cells, signed numeric money and omitted private notes',()=>{
 let state=initialDemo(freshInputs(),draftRule);state=decide(state,state.run!.findings[0],'confirm','=PRIVATE_NOTE');state.inputs.batches[0].source='=HYPERLINK("https://example.invalid", "test")';
 const book=XLSX.read(reportWorkbook(billingReport(state)),{type:'array',cellFormula:true});expect(book.SheetNames).toHaveLength(8);expect(book.Sheets['Source references'].B2.t).toBe('s');expect(book.Sheets['Source references'].B2.f).toBeUndefined();expect(book.Sheets.Findings.G2.t).toBe('n');expect(JSON.stringify(book)).not.toContain('PRIVATE_NOTE');for(const sheet of Object.values(book.Sheets))for(const [address,cell] of Object.entries(sheet))if(!address.startsWith('!')){expect(cell.f).toBeUndefined();expect(cell.l).toBeUndefined();}
});

it.each(['dimension','printer','conditional'])('safely handles %s metadata without dropping worksheet values',async mode=>{const output=execFileSync('python3',['tests/rewrite-xlsx-fixture.py',mode],{input:Buffer.from(bytes())});const array=Uint8Array.from(output).buffer;const book=await parseWorkbook(array);expect(book.sheets[0].rows[1]).toEqual(['W1','2026-10-05','450']);});
it('accepts a parenthesized worksheet name in a local print/filter reference',async()=>{const buffer=bytes((book)=>{book.SheetNames[0]='Time (Oct)';book.Sheets['Time (Oct)']=book.Sheets.Time;delete book.Sheets.Time;book.Workbook={Names:[{Name:'_xlnm._FilterDatabase',Ref:"'Time (Oct)'!$A$1:$C$2"}]};});expect((await parseWorkbook(buffer)).sheets[0].rows).toHaveLength(2);});
