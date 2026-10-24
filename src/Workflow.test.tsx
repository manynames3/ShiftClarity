import {it,expect} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {TeamQueue,CaseFollowup} from './Workflow';
import type {PilotController,FollowupCase} from './ServerApp';
const item:FollowupCase={id:'CASE-ONE',kind:'finding',facility_id:'FAC-A',service_from:'2026-10-01',service_to_exclusive:'2026-10-11',reason_code:'APPROVED_RATE_MISMATCH',work_ids:['W1'],last_run_id:'OLD',source_ref:'FND-001',amount:'200.00',status:'resolved',owner:null,correction_reference:'INV-A-C01',verified_run_id:'NEW',version:2,updated_at:'2026-10-24T12:00:00Z'};
it('keeps the selected resolved case when older filter responses arrive late',async()=>{
 let mine!:(value:unknown)=>void,open!:(value:unknown)=>void;
 const pendingMine=new Promise(resolve=>{mine=resolve;}),pendingOpen=new Promise(resolve=>{open=resolve;});

 const pilot={session:{actor:'REVIEWER',roles:['reviewer'],csrf:'test',synthetic:true},members:['REVIEWER'],refresh:async()=>{},api:async(path:string)=>{
  if(path==='/api/v1/cases/CASE-ONE')return {case:item,events:[]};
  if(path.includes('scope=mine'))return pendingMine;
  if(path.includes('status=open'))return pendingOpen;
  return {cases:[item],next:null,approvals:[]};
 }} as PilotController;
 render(<TeamQueue pilot={pilot}/>);const user=userEvent.setup();
 await user.selectOptions(screen.getByRole('combobox',{name:'Show'}),'team');
 await user.selectOptions(screen.getByRole('combobox',{name:'Status'}),'resolved');
 await user.click(await screen.findByRole('button',{name:'Follow up'}));
 expect(await screen.findByText('INV-A-C01')).toBeInTheDocument();
 await act(async()=>{open({cases:[],next:null,approvals:[]});mine({cases:[],next:null,approvals:[]});});
 expect(screen.getByRole('region',{name:'Case follow-up'})).toHaveTextContent('INV-A-C01');
 expect(screen.getByRole('combobox',{name:'Status'})).toHaveValue('resolved');
});

it('offers a working retry when follow-up details cannot be loaded',async()=>{
 let attempts=0;
 const pilot={session:{actor:'REVIEWER',roles:['reviewer'],csrf:'test',synthetic:true},members:[],refresh:async()=>{},api:async<T,>()=>{if(++attempts===1)throw new Error('Follow-up service unavailable.');return {case:item,events:[]} as T;}} as unknown as PilotController;
 render(<CaseFollowup pilot={pilot} caseId={item.id}/>);
 expect(await screen.findByRole('alert')).toHaveTextContent('unavailable');
 await userEvent.setup().click(screen.getByRole('button',{name:'Retry follow-up'}));
 expect(await screen.findByText('INV-A-C01')).toBeInTheDocument();
 expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});
