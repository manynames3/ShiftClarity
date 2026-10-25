import type {LocalWorkbook} from './workbook';
import type {BillingReport} from '../domain/report';
function job<T>(payload:unknown,transfer:Transferable[]=[],signal?:AbortSignal):Promise<T>{return new Promise((resolve,reject)=>{
 const worker=new Worker(new URL('./workbook.worker.ts',import.meta.url),{type:'module'});let timer:ReturnType<typeof setTimeout>;
 const finish=()=>{clearTimeout(timer);worker.terminate();signal?.removeEventListener('abort',abort);};const abort=()=>{finish();reject(Error('Local workbook processing was cancelled.'));};
 worker.onmessage=event=>{finish();event.data.ok?resolve(event.data.value):reject(Error(event.data.error));};worker.onerror=()=>{finish();reject(Error('Workbook processing failed. Save a fresh values-only XLSX or use CSV UTF-8.'));};
 timer=setTimeout(()=>{finish();reject(Error('Workbook processing exceeded eight seconds. Use a smaller values-only export.'));},8000);
 if(signal?.aborted){abort();return;}signal?.addEventListener('abort',abort,{once:true});worker.postMessage(payload,transfer);
});}
export const readBrowserWorkbook=(buffer:ArrayBuffer,signal?:AbortSignal)=>job<LocalWorkbook>({operation:'read',buffer},[buffer],signal);
export const createBrowserWorkbook=(report:BillingReport)=>job<ArrayBuffer>({operation:'report',report});
