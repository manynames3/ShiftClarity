import {it,expect} from 'vitest';
import {nextPeriod,headerChanges} from './import-helpers';
it('proposes the next equal-length closed interval across a leap day',()=>{expect(nextPeriod('2028-02-22','2028-02-29')).toEqual({service_from:'2028-02-29',service_to:'2028-03-06'});expect(()=>nextPeriod('2026-10-11','2026-10-05')).toThrow();});
it('distinguishes added, removed and reordered headers',()=>{expect(headerChanges(['A','B'],['B','C'])).toEqual({added:['C'],removed:['A'],reordered:false});expect(headerChanges(['A','B'],['B','A']).reordered).toBe(true);});
