import work from '../../handoff/data/synthetic/work_records.json';
import invoices from '../../handoff/data/synthetic/invoice_lines.json';
import rules from '../../handoff/data/synthetic/rate_rules.json';
import batches from '../../handoff/data/synthetic/import_batches.json';
import excerpts from '../../handoff/data/synthetic/source_excerpts.json';
import manifest from '../../handoff/data/synthetic/manifest.json';
import draft from '../../handoff/data/synthetic/draft_rule.json';
import facilities from '../../handoff/data/synthetic/facilities.json';
import type {Inputs, Rule} from '../domain/types';
export const fixture:Inputs={work,invoices,rules,batches,excerpts,manifest};
export const draftRule:Rule=draft;
export {facilities};
export const freshInputs=():Inputs=>structuredClone(fixture);
export const facilityName=(id:string)=>facilities.find(f=>f.id===id)?.name||id;
const approvedFiles=import.meta.glob(['../../handoff/data/synthetic/*.{json,csv,txt}','!../../handoff/data/synthetic/expected_results.json'],{query:'?raw',import:'default',eager:true}) as Record<string,string>;
export function validateFixtureFile(name:string,text:string):{accepted:boolean;reason:string} {
  const canonical=approvedFiles[`../../handoff/data/synthetic/${name}`];
  if(!canonical)return {accepted:false,reason:'Nonfixture file rejected. Real-data import is not enabled.'};
  if(text!==canonical)return {accepted:false,reason:'Fixture content differs from the supplied file. No run was published.'};
  return {accepted:true,reason:'Selected supplied file validated locally; complete canonical snapshot reloaded. Identical records are not duplicated.'};
}

import draftDocument from "../../handoff/data/synthetic/DOC-004.txt?raw";
export const fullDraftLines=draftDocument.trim().split("\n");
