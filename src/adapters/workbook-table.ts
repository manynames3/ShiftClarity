import type {WorkbookSheet} from './workbook';
import {tableFromRows} from './local-tables';
export function workbookTable(name:string,sheet:WorkbookSheet,headerRow:number,sha256:string){
 if(!Number.isInteger(headerRow)||headerRow<1||headerRow>20||headerRow>sheet.rows.length)throw Error('Choose the worksheet’s column-header row, from 1 to 20.');
 const raw=sheet.rows.slice(headerRow-1),width=raw[0].reduce((last,value,index)=>value.trim()!==''?index+1:last,0);
 if(raw.some(row=>row.slice(width).some(v=>v.trim()!=='')))throw Error('Data exists outside the selected header columns. Choose the correct header row or export a values-only table.');
 const rows=raw.map((values,index)=>({values:values.slice(0,width),row:index+headerRow})).filter((row,index)=>index===0||row.values.some(v=>v.trim()!==''));
 const table=tableFromRows((name+' / '+sheet.name).slice(0,80),rows.map(r=>r.values),sha256);table.rows.forEach((row,index)=>row.number=rows[index+1].row);table.numeric=Object.fromEntries(table.rows.map(row=>[row.number,(sheet.numeric?.[row.number-1]||[]).map(col=>table.headers[col])]));table.skipped_rows=sheet.rows.slice(0,headerRow-1).filter(row=>row.some(v=>v.trim()!=='')).length;return table;
}
