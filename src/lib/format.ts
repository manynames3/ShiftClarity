function dateOnly(value:string){
 const match=/^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
 if(!match)return null;
 const [,year,month,day]=match;
 const date=new Date(Date.UTC(Number(year),Number(month)-1,Number(day)));
 if(date.getUTCFullYear()!==Number(year)||date.getUTCMonth()!==Number(month)-1||date.getUTCDate()!==Number(day))return null;
 return date;
}

const dateParts=(date:Date)=>({
 year:date.getUTCFullYear(),
 month:new Intl.DateTimeFormat('en-US',{month:'short',timeZone:'UTC'}).format(date),
 day:date.getUTCDate(),
});

export function formatDate(value:string){
 const date=dateOnly(value.slice(0,10));
 if(!date)return value;
 const {year,month,day}=dateParts(date);
 return `${month} ${day}, ${year}`;
}

/** Formats the half-open service interval as an inclusive date range. */
export function formatDateRange(start:string,endExclusive:string){
 const first=dateOnly(start),exclusiveEnd=dateOnly(endExclusive);
 if(!first||!exclusiveEnd)return `${formatDate(start)}–${formatDate(endExclusive)}`;
 const last=new Date(exclusiveEnd);
 last.setUTCDate(last.getUTCDate()-1);
 if(last<first)return `${formatDate(start)}–${formatDate(endExclusive)}`;
 const a=dateParts(first),b=dateParts(last);
 if(a.year===b.year&&a.month===b.month)return `${a.month} ${a.day}–${b.day}, ${a.year}`;
 if(a.year===b.year)return `${a.month} ${a.day}–${b.month} ${b.day}, ${a.year}`;
 return `${a.month} ${a.day}, ${a.year}–${b.month} ${b.day}, ${b.year}`;
}

export function formatDateSpan(start:string,endInclusive:string){
 const last=dateOnly(endInclusive);
 if(!last)return `${formatDate(start)}–${formatDate(endInclusive)}`;
 if(start===endInclusive)return formatDate(start);
 last.setUTCDate(last.getUTCDate()+1);
 return formatDateRange(start,last.toISOString().slice(0,10));
}

export function formatTimestamp(value:string,timeZone='America/New_York'){
 const date=new Date(value);
 if(Number.isNaN(date.getTime()))return value;
 try{
  const parts=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
   timeZone,month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short',
  }).formatToParts(date).map(part=>[part.type,part.value]));
  return `${parts.month} ${parts.day}, ${parts.year}, ${parts.hour}:${parts.minute} ${parts.dayPeriod} ${parts.timeZoneName}`;
 }catch{return value;}
}
