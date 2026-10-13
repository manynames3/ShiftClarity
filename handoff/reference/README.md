# Canonical visual references

Open `index.html` locally. It is self-contained and uses no API or backend. The screen selector or top links navigate between seven design-reference views. These are not seven mandatory app modules: Brand and Product intro establish identity only.

The 29 PNGs reproduce the reference at 1440, 1280, 1024 and 390 pixel widths, plus the second evidence case at 1440. `viewport-manifest.json` maps every PNG to its state and viewport. Full-page captures are intentionally taller than their viewport.

## Build authority
Use domain rules and scope lock first, then tokens and these actual HTML/PNG references. Do not use any separately generated presentation artwork as a pixel-level build specification. No decorative elements may override readable records or correct coverage semantics.

## What works in this HTML
Screen navigation, facility/search filters, evidence tabs, mobile menu and explanatory dialogs. Review buttons explicitly state that this file does not save decisions. The future functional demo must implement the specified local transitions rather than carry over illustrative dialogs.

## Responsive behavior
Wide view: persistent navy sidebar and light operational workspace. At 390 px: compact top bar, two-column summary cards, stacked finding record cards, stacked evidence and review controls. Evidence-line tables use contained scrolling, never horizontal page overflow. At 320 px content still reflows.

## Rendering limits
Inter was installed in the rendering environment. Outlined wordmarks are independent of font availability; other text uses a system fallback if Inter is not present. Obtain an appropriately licensed verified font source during implementation for exact typography parity. Font files are not included.

Browser policy in this execution environment blocked full file/URL navigations. Each view was therefore rendered independently from the same HTML, in-page interactions were exercised, and route targets were checked. Full browser route transitions remain to be exercised in the implementation environment.
