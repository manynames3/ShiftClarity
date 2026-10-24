# A varied fictional staffing billing review

Two invented facilities, 18 work records, 20 invoice lines and seven approved hourly rate versions. Hours range from 2 to 12; RN, LPN and CNA work uses explicit regular, overtime and weekend rates. This is deliberately exception-rich evaluation data, not a claim about typical staffing billing error rates.

Use the existing signed-in ShiftClarity pilot: choose **Files & rate approvals**, facility **ALL**, October 1-15, 2026, files current through **October 21 at 17:00 UTC** and billing cutoff **October 20 at 12:00 UTC**. Declare complete work and invoice coverage for this fictional example. Optional independent controls are **136 work hours** and **$8,328.25 signed posted invoices**.

Upload `rates.csv`, `work.csv` and `invoices.csv` under their matching categories. Use ISO dates, decimal-point USD, hours and exclusive rate end dates. Confirm every mapping, including credit/rebill/void meanings. Have a separate permitted account inspect and approve the new rates, then accept sources and run the review. The voided invoice is excluded; signed credits are not added as revenue.

| Case | Expected | Invoiced | Difference |
|---|---:|---:|---:|
| Bayside RN, 7.5 hours at $72.50 vs $70 billed | $543.75 | $525.00 | +$18.75 |
| Bayside RN, 11.5 hours at the same dated terms | $833.75 | $805.00 | +$28.75 |
| Two overtime hours billed at the regular rate | $217.50 | $145.00 | +$72.50 |
| Approved eight-hour shift absent after the cutoff | $580.00 | $0.00 | +$580.00 |
| Riverbend RN, 9.5 hours billed above the agreed rate | $774.25 | $807.50 | -$33.25 |
| Weekend RN hours billed at the regular rate | $706.00 | $652.00 | +$54.00 |
| CNA shift: four of eight approved hours invoiced | $278.00 | $139.00 | +$139.00 |
| Original $1,020 invoice reversed; $966 rebill still short | $978.00 | $966.00 net | +$12.00 |

Eight other shifts align. An unsupported callback and a pending time approval receive no financial estimate. Source coverage remains separate from the discrepancy calculation.

Expected totals: **$905 potential underbilling**, **$33.25 potential overbilling**, **16 of 18 work records evaluated**, seven findings and two coverage gaps. Evaluated expected billing is **$8,626.00** against **$7,754.25** evaluated invoice allocations. All posted invoices total **$8,328.25**, including unchecked work. Do not subtract the all-posted total from the evaluated expected amount.

The sample report contains three explicitly fictional confirmed reviews (two underbilling findings and the overbilling finding), one evidence request for the remaining rebill difference, and three findings still awaiting review. Reproduce these through the normal review actions if desired; imported values never grant review or approval authority. Reviewer notes and worker identities remain omitted from exports by default.

`expected-results.json` is an independently authored test oracle, never an input to ShiftClarity's calculations. The original compact FAC-A/$200 walkthrough remains separate. These are billing review reports, not invoices issued to clients, collection records or vendor-certified exports.
