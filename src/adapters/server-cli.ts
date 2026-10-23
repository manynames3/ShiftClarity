import {readFileSync} from 'node:fs';
import {parseCustom} from './custom';
import {initialDemo,publish,decide,approveRule,rejectRule,exportReviews} from '../domain/demo';
import type {Demo} from '../domain/demo';
import {approveRateBatch} from '../domain/rate-approval';
const request=JSON.parse(readFileSync(0,'utf8'));
try {
 let result:unknown;
 switch(request.operation){
  case 'validate': result=parseCustom(request.text); break;
  case 'seed': result=initialDemo(request.inputs,request.draft); break;
  case 'publish': {
   const state=publish(request.state,request.inputs,{actor:'SYSTEM',timestamp:request.timestamp});
   if(state.importState==='failed')throw new Error('Calculation validation failed');
   result=state;break;
  }
  case 'decide': {
   const state=request.state as Demo;
   const finding=state.run?.findings.find(f=>f.id===request.finding);
   if(!finding||finding.fingerprint!==request.fingerprint)throw new Error('Evidence conflict');
   result=decide(state,finding,request.action,request.reason,request.owner,request.version,{actor:request.actor,timestamp:request.timestamp});break;
  }
  case 'approve': result=approveRule(request.state,request.actor,true,request.timestamp,request.reason);break;
  case 'reject': result=rejectRule(request.state,request.actor,request.reason,true,request.timestamp);break;
  case 'export': result=exportReviews(request.state);break;
  case 'approve_imported_rates': result=approveRateBatch(request.rules,request.existing,request.excerpt_ids,request.actor,request.timestamp);break;
  default:throw new Error('Unknown operation');
 }
 process.stdout.write(JSON.stringify({ok:true,result}));
}catch(error){
 // Input values and exception strings never cross the parser process boundary.
 const message=error instanceof Error?error.message:'';
 const code=request.operation!=='validate'?'VALIDATION_OR_CONFLICT':
  message.startsWith('Invalid JSON')?'INVALID_JSON':
  message.includes('unsupported field')?'UNSUPPORTED_FIELDS':
  /control total|row count/.test(message)?'SOURCE_CONTROLS':'INVALID_SCHEMA';
 process.stdout.write(JSON.stringify({ok:false,error:code}));
 process.exitCode=1;
}
