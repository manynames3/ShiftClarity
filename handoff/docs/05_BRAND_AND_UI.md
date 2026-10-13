# 05 · Brand and interface contract

## Design premise
**Calm precision, visible evidence.** ShiftClarity is a high-end operations product, not a money dashboard. Its visual relationship to Supreme AI Ventures is deliberate: deep navy, restrained teal, white surfaces, editorial typography, precise dividers and modest corner radii. Product-specific symbol and information design make it a distinct brand.

The live requested domain could not be retrieved in this environment. The actual `manynames3/supremeai` repository was inspected. Current enterprise CSS overrides use navy `#142333`, teal `#006C78`, dark teal `#004E5A`, muted `#526171` and line `#D9DFE5`. Earlier pale-teal root tokens were not mistaken for the final enterprise override. See `brand/parent-brand.json` and sources.

## Logo system
Use `brand/shiftclarity-mark.svg`, the outlined wordmarks and their inverse variants. The original mark is an **alignment link**: two precisely opposed open forms resolving into one unit. It represents agreement and connected evidence. It is not a dollar symbol, medical cross, crown, generic shield or certification mark.

Minimum displayed mark size 24 px, preferred 32–40 px. Wordmark preferred height 30–36 px in navigation. Clear space: at least one-quarter of the mark's height. Never rotate, stretch, independently recolor components, add gradients/shadows, or pair with an unrelated icon. The parent endorsement is subordinate: "A Supreme AI Ventures product" or "by Supreme AI Ventures".

The brand is a working proposal. No trademark clearance is claimed. No supplied files are font files. Outlined wordmarks preserve their shape without requiring a font install.

## Tokens (authoritative files in brand/)
Ink/nav `#142333`; primary teal `#006C78`; hover teal `#004E5A`; canvas `#F5F7F8`; surface white; muted `#526171`; line `#D9DFE5`; pale teal `#EAF4F3`. Amber identifies attention, not opportunity. Red is reserved for destructive/error conditions and overbilling semantics with explicit labels, not constant alarm.

Typography: **Inter** for UI, with ui-sans/system fallbacks. Parent site declares Inter. Display uses Inter Display/Inter with medium weight and modest negative tracking. Code/IDs may use ui-monospace. Do not switch the app to a serif or compressed typeface. Font files are not bundled. Obtain appropriate licensed web fonts through a verified package/source during implementation, then lock the source/version. System fallback is functional but may not match screenshot line lengths exactly.

Scale: marketing heading 52–64 px; workspace heading 30–34; section heading 18–20; body/table 14–16; labels 12–13. Uppercase column/section identifiers may use 11 px, but record values and explanations must remain at least 12 px, with primary table values at 14 px. Tabular numerals on amounts/hours, right-aligned numeric columns. Application radius 4/6/8 px; status tags can be pills but are small and infrequent. Buttons 44 px minimum design target; icons normally 18 px with consistent strokes.

Spacing: 4/8/12/16/20/24/32/40/48/64. Standard content gutter 32 px desktop, 24 px tablet, 16 px mobile. Desktop sidebar 228 px; top bar 68 px. Maximum content width 1440 px, with tables allowed to use the workspace width. Borders communicate grouping more than shadows. One subtle shadow may separate a dialog or document preview. No decorative glass/blur.

## Canonical screens
`reference/index.html` is a static, local, navigable DESIGN REFERENCE. Its actions explain intended behavior rather than silently pretending to store records. Codex must implement those behaviors in the actual demo.

1. **Workspace:** coverage-first summary; two financial findings; two coverage gaps; freshness/run context; no recovered-money KPI or fake trend chart.
2. **Evidence:** signed amendment excerpt, expected/invoiced comparison, concrete affected rows, review controls, source version and decision history. The amount is contextual, not celebratory.
3. **Inputs & rules:** three import batches, validation status, approved rules, source ranges and current run. No unimplemented vendor connection logos.
4. **Rule approval:** excerpt beside the exact draft fields, effective interval, author/approver separation, conflict and rejection states.
5. **Coverage:** explicit categories, the denominator, unsupported callback and missing approval tasks. No estimate for unknown financial impact.
6. **Brand board:** wordmark, colors, typography and tone. A brand reference, not an app route requirement.
7. **Product intro:** restrained product pitch in the parent-company visual family. Direction only; no public landing/pricing build authorized.

## Reference data lock
All canonical pages use the same snapshot: 14 records, 148 h, 12 checked records / 124 h, 2 financial findings, 2 coverage gaps. Aligned 6 records, flagged 6, unsupported 1, not evaluated 1. Rate finding 200.00; missing-billing finding 1560.00; neither is recovered cash. Use data IDs from the synthetic files. Never replace it with random SaaS metrics or invented percentage growth.

## Interaction and copy
Use "Rule-checked", "Aligned under checked rules", "Needs review", "Not evaluated", "Unsupported component", "Source incomplete" and "Potential discrepancy". Avoid "100% accurate", "verified everything", "AI detected lost revenue" and "money recovered".

CTA hierarchy: one strong primary per local task; secondary neutral outline; destructive actions require confirmation. Confirming a finding does not send a message or edit an invoice. Dismiss requires an explanation. Evidence tab names describe the actual source. External links need an explicit destination and accessible label. No dead controls.

Empty queue with incomplete coverage: "No discrepancies found in the checked records. Some records still need evidence." Never show a large green "All clear". Imported fixture files visibly say synthetic. Dates use explicit year on evidence; timestamps show timezone in run details. Do not use relative time based on the real clock for the fixed demo.

## Accessibility and responsive contract
Target WCAG 2.2 AA. Ordinary text contrast >=4.5:1; large text >=3:1; interactive boundaries/status icons/focus have adequate contrast. The palette alone is not proof of full compliance. Test real rendered states and keyboard paths. Text labels accompany color. Charts include text counts and cannot be the sole representation of coverage.

At 1440×1000: sidebar + wide workspace; evidence columns approximately 60/40. At 1280×900: preserve evidence priority and readable 14px body. At 1024×900: compact navigation, stacked lower panels; do not shrink text to squeeze. At 390×844: top navigation/menu, stacked summary/evidence, and findings presented as readable stacked record cards. Evidence-detail tables may use a labeled contained horizontal scroller; no horizontal page overflow. At 320 px content still reflows. Controls retain keyboard focus after routing, dialogs trap/restore focus, Escape closes nondestructive dialogs.

## Motion
Task-focused only: 120–180 ms opacity/color transitions, up to 200 ms panel entrance. No scroll hijacking, parallax, animated numbers, endless gradient motion or chart theatrics. Honor `prefers-reduced-motion`. A premium interface is quick and stable, not cinematic. Three.js/GSAP are unnecessary inside this operational app.

## Visual acceptance checklist
Use exact mark and tokens; align page titles/table columns/buttons; preserve navy sidebar + light content; no clipping at canonical widths; no awkward wraps in status/action labels; no unexplained mixed corner radii; evidence/source text readable; empty/error/loading/denied states designed; money calculations fit without truncation; file names wrap gracefully; all generated screenshots match the shared data snapshot. Screenshots guide layout, while domain requirements override any incidental illustrative text.
