import type {Finding, Reviews, ReviewState} from './domain/types';
import {findingKey} from './domain/demo';
export const stateLabel:Record<ReviewState,string>={needs_review:'Needs review',confirmed:'Confirmed discrepancy',dismissed:'Dismissed',evidence_requested:'Evidence requested'};
export function formatMoney(value:string,signed=false){const negative=value.startsWith('-'),[whole,cents]=value.replace('-','').split('.');return `${negative?'-':signed?'+':''}$${whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')}.${cents}`;}
export const logicalKey=findingKey;
export const reviewFor=(f:Finding,r:Reviews)=>r[logicalKey(f)]||{state:'needs_review' as const,fingerprint:f.fingerprint,history:[],version:1};
export const titleFor=(f:Finding)=>f.reason_code==='APPROVED_WORK_NOT_IN_INVOICE_EXTRACT'?'Approved work not invoiced':f.reason_code==='APPROVED_RATE_MISMATCH'?'Rate change not reflected':'Invoice amount differs';
