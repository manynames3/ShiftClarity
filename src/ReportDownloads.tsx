import {createBrowserWorkbook} from './adapters/browser-workbook';
import {useMemo,useState} from 'react';
import type {Demo} from './domain/demo';
import {billingReport,reportCsv,reportLimit} from './domain/report';
import type {BillingReport,ReportCell} from './domain/report';
import {Dialog} from './components';
import {displayUserText,formatMoney} from './presentation';
import './reports.css';

function save(blob:Blob,filename:string){
 const href=URL.createObjectURL(blob),a=document.createElement('a');a.href=href;a.download=filename;a.click();window.setTimeout(()=>URL.revokeObjectURL(href),1000);
}

export function ReportDownloads({state,secure,onClose}:{state:Demo;secure:boolean;onClose:()=>void}){
 const [notes,setNotes]=useState(false),[busy,setBusy]=useState(''),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const report=useMemo(()=>billingReport(state,notes),[state,notes]);
 async function localExcel(){setBusy('xlsx');setError('');try{save(new Blob([await createBrowserWorkbook(report)],{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}),'ShiftClarity-billing-review.xlsx');setNotice('Excel report downloaded locally.');}catch(e){setError((e as Error).message);}finally{setBusy('');}}
 async function download(format:'xlsx'|'pdf'){
  setBusy(format);setError('');setNotice('');
  try{
   const response=await fetch('/api/v1/runs/'+encodeURIComponent(report.runId)+'/report.'+format+'?include_notes='+notes,{credentials:'same-origin'});
   if(!response.ok){const body=await response.json().catch(()=>null);throw new Error(body?.detail||'Report unavailable. Refresh your session and try again.');}
   save(await response.blob(),'ShiftClarity-billing-review.'+format);setNotice('Report downloaded.');
  }catch(e){setError((e as Error).message);}finally{setBusy('');}
 }
 return <Dialog title="Download billing review" secure={secure} localData={!state.inputs.manifest.synthetic} onClose={onClose} className="report-dialog">
  <button className="report-close" aria-label="Close report" onClick={onClose}><span aria-hidden="true">×</span></button>
  <div className="report-controls">
   <p>All findings, current decisions and coverage gaps. Search and facility filters do not limit the report. Worker identities are omitted.</p>
   <label className="report-notes"><input type="checkbox" checked={notes} onChange={e=>setNotes(e.target.checked)} disabled={!!busy}/>Include reviewer notes I’m authorized to share</label>
   {state.stale&&<p className="report-stale" role="alert">Stale results: the previous completed run is retained. Reports carry this warning.</p>}
   {secure?<div className="report-actions"><button className="btn btn-primary" disabled={!!busy} onClick={()=>void download('pdf')}>{busy==='pdf'?'Preparing PDF…':'Download PDF'}</button><button className="btn" disabled={!!busy} onClick={()=>void download('xlsx')}>{busy==='xlsx'?'Preparing Excel…':'Download Excel'}</button></div>:<><p className="report-local-note">Created in your browser. No records are uploaded. For PDF, choose “Save as PDF” in the print dialog.</p><div className="report-actions"><button className="btn btn-primary" onClick={()=>window.print()}>Print / save PDF</button><button className="btn" disabled={!!busy} onClick={()=>void localExcel()}>{busy==='xlsx'?'Preparing Excel…':'Download Excel'}</button><button className="btn" onClick={()=>{save(new Blob([reportCsv(report)],{type:'text/csv;charset=utf-8'}),'ShiftClarity-billing-review.csv');setNotice('CSV report downloaded. Open it in Excel or another spreadsheet app.');}}>Download CSV</button></div></>}
   {error&&<p className="error" role="alert">{displayUserText(error)}</p>}{notice&&<p role="status">{notice}</p>}
  </div>
  {!secure&&<PrintableReport report={report}/>}
 </Dialog>;
}

function ReportTable({headers,rows}:{headers:string[];rows:ReportCell[][]}){
 return rows.length?<table><thead><tr>{headers.map(h=><th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={index}>{row.map((value,i)=><td key={i}>{value===null?'Not estimated':value}</td>)}</tr>)}</tbody></table>:<p>None in this run.</p>;
}

function PrintableReport({report}:{report:BillingReport}){
 const find=(name:string)=>report.tables.find(t=>t.name===name)!,summary=Object.fromEntries(find('Overview').rows),money=(value:ReportCell)=>formatMoney(Number(value).toFixed(2));
 return <article className="billing-print-report" aria-label="Billing report preview">
  <header><img src="/brand/shiftclarity-report-logo.png" width="180" alt="ShiftClarity"/><span>{report.synthetic?'Fictional evaluation':'User-supplied local preview'}</span></header>
  <h1>Billing review</h1><p>Service period: {summary['Service from (inclusive)']} to {summary['Service to (exclusive)']} (end exclusive)<br/>{report.runId} · USD · Prepared {report.generatedAt}</p>
  {report.stale&&<p className="report-stale">STALE RESULTS: Previous completed run retained. Rerun validated evidence before making a decision.</p>}
  <dl className="report-metrics"><div><dt>Potential underbilling</dt><dd>{money(summary['Potential underbilling before review exclusions (USD)'])}</dd></div><div><dt>Potential overbilling</dt><dd>{money(summary['Potential overbilling before review exclusions (USD)'])}</dd></div><div><dt>Work evaluated</dt><dd>{summary['Records evaluated']} / {summary['Records received']}</dd></div></dl>
  <p className="report-limit">{reportLimit}</p>
  <h2>What this review establishes</h2><p>{summary['Findings']} findings. {summary['Confirmed discrepancy']} confirmed; {summary['Not a discrepancy']} dismissed; {summary['Evidence requested']} awaiting evidence; {summary['Needs review']} need review. All states are included; potential totals are before review exclusions.</p>
  <ReportTable headers={['Evaluated-work comparison','Amount USD']} rows={[
   ['Expected under approved terms',money(summary['Expected on evaluated work (USD)'])],['Signed invoice allocations on evaluated work',money(summary['Net invoiced on evaluated work (USD)'])],
   ['Reviewer-confirmed underbilling difference',money(summary['Reviewer-confirmed underbilling difference (USD)'])],['Reviewer-confirmed overbilling difference',money(summary['Reviewer-confirmed overbilling difference (USD)'])]
  ]}/><p>Reviewer confirmation records a review. It does not adjust an invoice or establish collected funds.</p>
  <h2>Findings and calculations</h2>
  {find('Findings').rows.length?find('Findings').rows.map(row=><section className="report-finding" key={String(row[0])}><h3>{row[0]} · {row[1]} · {row[2]}</h3><p>{row[3]} · Rate version {row[5]}</p><ReportTable headers={['Expected','Net invoiced','Signed difference']} rows={[[money(row[6]),money(row[7]),money(row[8])]]}/><ReportTable headers={['Work','Service date','Minutes','Hours*','Expected','Invoiced','Difference']} rows={find('Work calculations').rows.filter(r=>report.findingWork[String(row[0])].includes(String(r[0]))).map(r=>[r[0],r[2],r[5],Number(r[6]).toFixed(2),money(r[11]),money(r[12]),money(r[13])])}/></section>):<p>No calculated findings. Review the coverage gaps before interpreting this as agreement.</p>}
  <p className="report-limit">Expected = exact approved hourly rate x minutes / 60, less signed posted invoice allocations. *Hours display two decimals; calculations use whole minutes. Collectibility is not established.</p>
  <h2>Coverage and evidence limits</h2><p>{summary['Hours received']} hours received; {summary['Hours evaluated']} hours evaluated. Invoice coverage: {summary['Coverage declaration']}. Source as of {summary['Source current through']}; billing cutoff {summary['Billing cutoff']}.</p>
  <ReportTable headers={['Work reference','Coverage gap','Estimate']} rows={find('Coverage gaps').rows.map(r=>[r[1],r[3],r[4]])}/>
  <h2>Invoice allocations</h2><ReportTable headers={find('Invoice allocations').headers} rows={find('Invoice allocations').rows.map(r=>[...r.slice(0,3),money(r[3]),r[4]])}/>
  {report.tables.filter(t=>t.name==='Non-hourly invoice lines'||t.name==='Invoice source lines').map(t=><section className="report-support-table" key={t.name}><h2>{t.name}</h2><p>{t.name==='Non-hourly invoice lines'?'Retained in source totals, outside hourly comparison. No difference is estimated.':'All supplied invoice rows, including unallocated and non-hourly lines. Batch references identify the original file hash.'}</p>{t.name==='Invoice source lines'?<ReportTable headers={['Invoice / line','Facility','Posting status','Signed USD','Billing scope']} rows={t.rows.map(row=>[row[0]+' / '+row[1],row[2],row[3],money(row[5]),row[8]])}/>:<ReportTable headers={t.headers} rows={t.rows.map(row=>[...row.slice(0,4),money(row[4]),row[5]])}/>}<p className="report-limit">Full normalized invoice columns are available in the Excel/CSV report.</p></section>)}
  <h2>Applicable rate terms</h2>{find('Rate terms').rows.map(r=><div className="report-rate" key={String(r[0])}><h3>{r[0]} · {r[2]} · {r[3]} / {r[4]} · ${Number(r[5]).toFixed(4)} per hour</h3><p>Effective {r[6]} to {r[7]||'open'} (end exclusive). Source authorized: {r[8]||'not supplied'}. {report.synthetic?'System approved at':'Supplied source approval date'} {r[9]||'not supplied'} by {r[11]||'not supplied'}. Evidence: {r[12]}.</p></div>)}
  <h2>Source references</h2><p>Source batch references. CSV evaluations include original-file SHA-256 references; manually entered or normalized JSON previews may not.</p>{find('Source references').rows.map(row=><div className="report-source" key={String(row[0])}><h3>{row[0]} · {String(row[1]).split(' · SHA-256 ')[0]}</h3><p>{row[2]} records · Source as of {row[3]} · {row[4]}</p>{String(row[1]).includes(' · SHA-256 ')&&<p className="report-limit">Original SHA-256: {String(row[1]).split(' · SHA-256 ')[1]}</p>}</div>)}
  <h2>Review history</h2><p>Reviewer notes: {report.notesIncluded?'explicitly included':'omitted'}. Worker identities: omitted.</p><ReportTable headers={find('Review history').headers} rows={find('Review history').rows}/>
  <footer>{report.runId} · {summary['Calculation engine']} · {summary['Data boundary']}<br/>{reportLimit}</footer>
 </article>;
}
