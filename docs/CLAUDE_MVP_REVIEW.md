# Claude review and disposition

October 23, 2026. Official local Claude Code 2.1.296, subscription-authenticated, paid Extra Usage confirmed disabled. Claude supplied read-only plan/brief and code reviews; Codex implemented and ran verification. Claude ran no tests, made no edits and had no deployment authority. No credentials or customer records were shared.

| Finding from the code review | Verified disposition |
|---|---|
| Cross-session rate approvals can race | Workspace lock acquired before reading registered terms; concurrent overlapping approvals regression allows one success and one actionable conflict. |
| Rejected acceptance can silently invalidate prior review | Shared revision-conflict preflight at validation; nonvalidated acceptance returns a useful error. Guided import failure preserves the earlier workspace; legacy JSON failure behavior stays tested. |
| Raw previews outlive original-file retention | Previews gated by source-read roles while staged and removed from the accepted file snapshot. Derived immutable evidence has an explicit owner-purge policy. |
| Saved profiles omit new source values | Fetch values from the current file, retain known custom mappings, expose new entries for explicit choice. Browser repeats a period using new RG code. |
| Time/credit/authorization conventions cause adoption friction | Explain exact whole minutes and signed credit amounts; support explicitly negative credit quantities as absolute minutes; allow a confirmed fixed source authorization date. No inferred rounding or credit amount sign. |
| Recurring PDF hours overflow | Display two-decimal hours beside exact integer minutes; calculations still use the shared engine. |
| Retention can race acceptance or lose retries | Lock sessions before files; commit denial tombstones before deleting bytes; retain keys on deletion failure and test retry. |
| Sensitive header checks are too narrow | Block exact generic personal-name/contact/date-of-birth headers in addition to clinical/identity fields. Facility Name is not blocked merely for containing Name. Header checks never replace minimization or authorization. |

Additional questions: prior-period report navigation is explicitly unimplemented; download the current report before advancing. Semicolon/DMY/decimal-comma/minute conventions have a targeted regression. Failed parser requests and previews now consume a serialized, committed hourly attempt budget, in addition to subprocess limits. Original demo verification is recorded separately in [VERIFICATION.md](VERIFICATION.md).

The review is an independent engineering opinion, not a security audit or real-customer accuracy measurement. Remaining customer gates are in [PILOT_GATES.md](PILOT_GATES.md).
