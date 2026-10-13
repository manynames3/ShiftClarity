# 08 · Private walkthrough for William

## Opening (20 seconds)
"I built this around a specific question: when a facility agreement changes, do the right rates reach the right invoices? It works alongside the systems you already use. These records are fictional, so this is not a claim that Assist has billing issues."

## 1 · Workspace (30 seconds)
"Here are the records received, what the rules could actually check, and the items that still need evidence." Show 14 shifts, 12 checked, 2 findings, 2 coverage gaps. Do not lead with a revenue number.

## 2 · Effective-date discrepancy (60 seconds)
Open FND-001. "This approved amendment begins October 5. Four ten-hour shifts used the old invoice rate, creating a $200 difference." Show excerpt, effective date, 65 vs 60, invoice allocations and the requirement for a human review.

Then show the control S010: work from October 4 correctly keeps the old rate even though it was entered later. Show S007–S009 correctly aligned to one aggregate invoice. "The point is to avoid creating work for your team with false alarms."

## 3 · Missing billing versus missing evidence (40 seconds)
FND-002 requires a passed billing cutoff and complete invoice coverage. The app identifies 24 approved hours not represented in the supplied invoice extract. It is a potential discrepancy, not recovered money.

Open coverage tasks. One record lacks approval; another has an unsupported callback component. "These are not called billing errors. The system tells us it needs more information."

## 4 · Decision (30 seconds)
Show confirm/dismiss/request-evidence and a reason. Nothing changes in the invoice system or gets sent automatically. Show local demo history, new evidence reopening the finding, and reset.

## Close
"How would your billing team check this today? Is it already handled by your current software, or does someone still compare records manually?"

## Discovery questions
Which tools and modules create the work and invoice records? Can they export the actual fields shown here? What is the billing cutoff and how do you verify an extract is complete? What agreements govern rate changes? What recent issue needed manual cross-checking? Would this overlap with the platform you are developing? Which billing specialist should validate the rule/matching model?

## Honest follow-on
Propose a fixed-scope paid diagnostic only after a real gap is described. The earlier $2,500 / $995 ideas are conversation starters, not commitments in the demo. Do not claim immediate ROI or use client records without agreed safeguards.
