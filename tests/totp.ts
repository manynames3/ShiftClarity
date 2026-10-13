// Test-only authenticator; product authentication is handled by the identity provider.
import {createHmac} from 'node:crypto';
export function totp(secret:string,time=Date.now()){
 const alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
 let bits='';
 for(const letter of secret.replaceAll(' ','').replaceAll('=','').toUpperCase())bits+=alphabet.indexOf(letter).toString(2).padStart(5,'0');
 const key=Buffer.from((bits.match(/.{8}/g)||[]).map(byte=>parseInt(byte,2)));
 const counter=Buffer.alloc(8);counter.writeBigUInt64BE(BigInt(Math.floor(time/30000)));
 const mac=createHmac('sha1',key).update(counter).digest(),offset=mac.at(-1)!&15;
 return ((mac.readUInt32BE(offset)&0x7fffffff)%1000000).toString().padStart(6,'0');
}
