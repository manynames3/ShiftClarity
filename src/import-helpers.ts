export function nextPeriod(from:string,toExclusive:string){
 const start=Date.parse(from),end=Date.parse(toExclusive),days=(end-start)/86400000;
 if(!Number.isInteger(days)||days<1||days>93)throw Error('The previous service period is invalid. Choose the next dates explicitly.');
 return {service_from:toExclusive,service_to:new Date(end+(days-1)*86400000).toISOString().slice(0,10)};
}
export function headerChanges(previous:string[],current:string[]){return {added:current.filter(h=>!previous.includes(h)),removed:previous.filter(h=>!current.includes(h)),reordered:previous.length===current.length&&previous.every(h=>current.includes(h))&&previous.some((h,i)=>current[i]!==h)};}
