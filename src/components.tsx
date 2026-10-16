import { useEffect, useRef } from 'react';
import type {ReactNode} from 'react';
import type {Manifest} from './domain/types';
import {paths} from './icons';
import {formatTimestamp} from './lib/format';
export function Icon({name}:{name:keyof typeof paths}){return <svg className="icon" viewBox="0 0 24 24" aria-hidden="true"><path d={paths[name]}/></svg>;}
export function Logo({inverse=false}:{inverse?:boolean}){return <img className="wordmark" src={`/brand/shiftclarity-wordmark${inverse?'-inverse':''}.svg`} alt="ShiftClarity"/>;}
export function Pill({children,type='neutral'}:{children:ReactNode;type?:string}){return <span className={`pill pill-${type}`}>{children}</span>;}
export function Link({children,to,kind=''}:{children:ReactNode;to:string;kind?:string}){return <a className={`btn ${kind}`} href={to}>{children}</a>;}
export function Foot({run='RUN-001',manifest,secure=false}:{run?:string;manifest?:Manifest;secure?:boolean}){return <div className="footnote"><span><Icon name="lock"/>{manifest&&!manifest.synthetic?'User-supplied local preview.':'Fictional records only.'} No source systems are connected.</span><span>{run} · {manifest?formatTimestamp(manifest.as_of,manifest.timezone):'Oct 12, 2026, 5:00 PM EDT'}</span></div>;}
export function PanelHead({title,children,detail}:{title:string;children?:ReactNode;detail?:string}){return <div className="panel-head"><div><h2>{title}</h2>{detail&&<p>{detail}</p>}</div>{children}</div>;}
export function Dialog({title,children,onClose,secure=false}:{title:string;children:ReactNode;onClose:()=>void;secure?:boolean}){
 const ref=useRef<HTMLDialogElement>(null),previousRef=useRef(document.activeElement as HTMLElement);
 useEffect(()=>{const el=ref.current!;const previous=previousRef.current;el.showModal();return()=>{el.close();previous?.focus();};},[]);
 return <dialog ref={ref} className="dialog" aria-labelledby="dialog-title" onCancel={e=>{e.preventDefault();onClose();}} onKeyDown={e=>{if(e.key!=='Tab')return;const focusable=[...ref.current!.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]')].filter(el=>el.getClientRects().length);const first=focusable[0],last=focusable.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last?.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first?.focus();}}}><div className="eyebrow">{secure?'Synthetic pilot · Server record':'Synthetic demo · local only'}</div><h2 id="dialog-title">{title}</h2>{children}<button className="btn" onClick={onClose}>Cancel</button></dialog>;
}
