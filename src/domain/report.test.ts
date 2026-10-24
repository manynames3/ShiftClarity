import {expect,it} from 'vitest';
import {freshInputs,draftRule} from '../adapters/fixtures';
import {decide,initialDemo,findingKey,publish,scenarioInputs} from './demo';
import {billingReport,reportCsv} from './report';

it('exports every finding and coverage gap before any review, without worker identities or raw fingerprints',()=>{
 const state=initialDemo(freshInputs(),draftRule),report=billingReport(state);
 expect(report.tables.map(t=>t.name)).toHaveLength(8);
 expect(report.tables.find(t=>t.name==='Findings')!.rows).toHaveLength(2);
 expect(report.tables.find(t=>t.name==='Coverage gaps')!.rows).toHaveLength(2);
 const summary=Object.fromEntries(report.tables[0].rows);
 expect(summary['Potential underbilling before review exclusions (USD)']).toBe(1760);
 expect(summary['Records evaluated']).toBe(12);
 expect(summary['Hours evaluated']).toBe(124);
 const text=JSON.stringify(report);
 for(const work of state.inputs.work)expect(text).not.toContain('"'+work.worker_id+'"');
 expect(text).not.toContain(state.run!.fingerprint);
});

it('reflects decisions, omits notes by default and rejects mismatched review attestations',()=>{
 let state=initialDemo(freshInputs(),draftRule);const f=state.run!.findings[0];
 state=decide(state,f,'confirm','=PRIVATE_NOTE <script>alert(1)</script>');
 const report=billingReport(state);
 expect(report.tables.find(t=>t.name==='Findings')!.rows[0][2]).toBe('Confirmed discrepancy');
 expect(JSON.stringify(report)).not.toContain('PRIVATE_NOTE');
 expect(JSON.stringify(billingReport(state,true))).toContain('=PRIVATE_NOTE <script>alert(1)</script>');
 const summary=Object.fromEntries(report.tables[0].rows);
 expect(summary['Reviewer-confirmed underbilling difference (USD)']).toBe(Number(f.discrepancy_amount));
 state.reviews[findingKey(f)].fingerprint='previous-evidence';
 expect(billingReport(state).tables.find(t=>t.name==='Findings')!.rows[0][2]).toBe('Needs review');
 expect(Object.fromEntries(billingReport(state).tables[0].rows)['Reviewer-confirmed underbilling difference (USD)']).toBe(0);
});

it('retains stale results and coverage limits, exports no-findings runs, and refuses absent runs',()=>{
 const state=initialDemo(freshInputs(),draftRule),stale=publish(state,scenarioInputs(freshInputs(),'failed'));
 expect(billingReport(stale).stale).toBe(true);
 expect(Object.fromEntries(billingReport(stale).tables[0].rows)['Result freshness']).toMatch(/^STALE/);
 const partial=publish(state,scenarioInputs(freshInputs(),'partial'));
 expect(billingReport(partial).tables.find(t=>t.name==='Findings')!.rows).toHaveLength(0);
 expect(billingReport(partial).tables.find(t=>t.name==='Coverage gaps')!.rows.length).toBeGreaterThan(0);
 expect(()=>billingReport({...state,run:null})).toThrow('No completed run');
 const local=structuredClone(state);local.run!.manifest.synthetic=false;
 expect(Object.fromEntries(billingReport(local).tables[0].rows)['Data boundary']).toMatch(/^User-supplied local preview/);
});

it('keeps spreadsheet text literal while retaining signed numeric amounts',()=>{
 let state=initialDemo(freshInputs(),draftRule);const f=state.run!.findings[0];
 state=decide(state,f,'confirm','  =HYPERLINK("https://example.invalid", "test")');
 state.inputs.batches[0].source='@SUM(1,2)';
 state.run!.allocations[0].amount='-33.25';
 const csv=reportCsv(billingReport(state,true));
 expect(csv.startsWith('\uFEFF')).toBe(true);
 expect(csv).toContain('"\'@SUM(1,2)"');
 expect(csv).toContain('"\'=HYPERLINK(""https://example.invalid"", ""test"")"');
 expect(csv).toContain(',-33.25,');
 expect(reportCsv(billingReport(state))).not.toContain('HYPERLINK');
});
