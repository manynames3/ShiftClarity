import {describe,expect,it} from 'vitest';
import {formatDate,formatDateRange,formatDateSpan,formatTimestamp} from './format';

describe('presentation date formatting',()=>{
 it('formats single dates without exposing ISO values',()=>{
  expect(formatDate('2026-10-13')).toBe('Oct 13, 2026');
 });

 it('formats half-open service intervals as inclusive ranges',()=>{
  expect(formatDateRange('2026-10-05','2026-10-09')).toBe('Oct 5–8, 2026');
  expect(formatDateRange('2026-10-01','2026-10-11')).toBe('Oct 1–10, 2026');
  expect(formatDateRange('2026-10-31','2026-11-03')).toBe('Oct 31–Nov 2, 2026');
  expect(formatDateRange('2026-12-31','2027-01-03')).toBe('Dec 31, 2026–Jan 2, 2027');
 });

 it('formats inclusive record spans and timestamps in the review timezone',()=>{
  expect(formatDateSpan('2026-10-05','2026-10-08')).toBe('Oct 5–8, 2026');
  expect(formatTimestamp('2026-10-12T17:00:00-04:00')).toBe('Oct 12, 2026, 5:00 PM EDT');
  expect(formatTimestamp('2026-10-12T16:00:00-04:00')).toBe('Oct 12, 2026, 4:00 PM EDT');
 });
});
