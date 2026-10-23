import type {Rule} from './types';
import {ratePattern} from './engine';

export function validateRateApproval(d:Rule,actor:string,existing:Rule[],excerptIds:string[]){
 if(!d.author_id||actor===d.author_id)throw new Error('A different person must approve this rule.');
 if(d.state!=='pending_approval'||!excerptIds.includes(d.source_excerpt_id)||!ratePattern.test(d.rate)||!/^\d{4}-\d{2}-\d{2}$/.test(d.effective_from))throw new Error('Valid pending terms and source evidence required.');
 if(d.effective_to&&d.effective_to<=d.effective_from)throw new Error('Effective end must follow start.');
 const ancestors=new Set<string>();let predecessor=d.supersedes?existing.find(r=>r.id===d.supersedes):undefined;
 if(d.supersedes&&(!predecessor||predecessor.facility_id!==d.facility_id||predecessor.role!==d.role||predecessor.component!==d.component||d.effective_from<=predecessor.effective_from))throw new Error('Invalid explicit supersession.');
 while(predecessor&&!ancestors.has(predecessor.id)){ancestors.add(predecessor.id);predecessor=existing.find(r=>r.id===predecessor!.supersedes);}
 if(existing.some(r=>r.id===d.id))throw new Error('Rate version is already registered.');
 if(existing.some(r=>r.state==='approved'&&!ancestors.has(r.id)&&r.facility_id===d.facility_id&&r.role===d.role&&r.component===d.component&&(!r.effective_to||r.effective_to>d.effective_from)&&(!d.effective_to||r.effective_from<d.effective_to)))throw new Error('CONFLICTING_APPROVED_RULES — Conflicting approved terms; resolve the interval or predecessor.');
}

export function approveRateBatch(candidates:Rule[],existing:Rule[],excerptIds:string[],actor:string,timestamp:string):Rule[]{
 const result:Rule[]=[];
 for(const candidate of [...candidates].sort((a,b)=>a.effective_from.localeCompare(b.effective_from)||a.id.localeCompare(b.id))){
  validateRateApproval(candidate,actor,[...existing,...result],excerptIds);
  if(candidate.authorization_date&&candidate.authorization_date>timestamp.slice(0,10))throw new Error('Source authorization date cannot follow the actual approval.');
  result.push({...candidate,state:'approved',approver_id:actor,approved_at:timestamp});
 }
 return result;
}
