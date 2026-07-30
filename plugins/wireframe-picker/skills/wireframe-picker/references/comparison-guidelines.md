# Comparison guidelines by requirement category

Covers two requirement groups so far: **visual identity** and **structural defaults** — both are global, decided-once, applied-everywhere decisions. Other groups (recurring component patterns, page-specific one-offs) aren't covered here yet.

## Shared principle

Never compare these as an isolated swatch or single element. Render each candidate inside a real, moderately representative screen with real-ish content. An abstract swatch or one oversized icon can look great alone and fall apart in context, or the reverse — the whole point is judging it where it will actually live.

## Visual identity

### Brand color
- Compare **three** real brand-hued roles together, not one: **primary**, **secondary**, and **accent** — each gets its own OKLCH 50-950 Tailwind-style ramp and its own applied UI elements, because each shows up in different places (primary: main CTA, active nav, links, focus rings; secondary: lower-emphasis actions, tab indicators; accent: badges, tertiary/outline actions). `muted`/`border` stay neutral-gray and `destructive` stays fixed semantic red — those aren't part of this comparison. Never compare as a flat color swatch alone — a color that looks fine as a flat square can fail once it's a button, a link, or a focus ring at a specific lightness step.
- Variants: 2-4 candidate hue combinations (each candidate = one primary+secondary+accent hue triple).
- Pattern: `.cards` grid for the picker screen; use [templates/mockups/brand-color-palette.html.tmpl](../scripts/templates/mockups/brand-color-palette.html.tmpl) for each candidate's content — fill in `{{PRIMARY_HUE}}`, `{{SECONDARY_HUE}}`, `{{ACCENT_HUE}}`, serve, screenshot, reference from the card. Verified: `oklch()` renders correctly and all three roles read as visually distinct in the Playwright chromium build already installed for this plugin.

### Typography / font pairing
- Render a specimen block — H1, H2, body paragraph, a data-table label, a button — never a heading alone. Pairings often break at small sizes or on numerals.
- Variants: 2-3. Font differences are visually loud; more than that is noise.
- Pattern: `.cards` grid for the picker screen; use [templates/mockups/font-specimen.html.tmpl](../scripts/templates/mockups/font-specimen.html.tmpl) for each candidate's content. **This must load a real webfont** (a Google Fonts `<link>`, already wired into the template) — setting `font-family` to an unloaded font name silently falls back to the system font and makes every candidate look identical. Verified: Google Fonts is reachable from this environment and a serif candidate rendered visibly distinct from the sans-serif fallback. Pass a longer wait when capturing so the font fetch finishes: `capture-screenshot.sh <url> <out.png> --wait-for-timeout 1500`.

### Icon style (outline vs. filled)
- Render a representative *set* of 5-8 icons together, at actual usage size (16-20px), in real contexts (nav rail, toolbar, empty state) — not one icon blown up large. Consistency across the set matters more than any single icon's shape.
- Variants: 2 (outline/filled), 3 if a duotone option exists.
- Pattern: `.cards` grid, each card a small icon-strip screenshot.

### Corner radius / shape language
- Render a composite strip of button + card + input + avatar together per radius value — radius reads very differently on small vs. large elements.
- Variants: 3-4 (sharp, subtle, rounded, pill).
- Pattern: `.cards` grid.

### Elevation style (flat vs. layered shadows)
- Render a scene with an actual z-order relationship — e.g. a card with a popover/dropdown open above it — never a single card floating alone. Elevation only reads meaningfully against something it's elevated over.
- Variants: 2-3 (flat/border-only, soft shadow, pronounced shadow).
- Pattern: `.split` for 2 variants (direct A/B), `.cards` for 3.

## Structural defaults

### Default layout (sidebar vs. top tabs)
- Render a full representative page with real-ish content, never an empty shell — layout choice interacts with content density and scan pattern, which an empty page can't show.
- Variants: 2-3.
- Pattern: `.cards` grid — the exact pattern already demoed and verified for this plugin.

### Navigation pattern (desktop rail/top-bar; mobile hamburger/bottom-tabs)
- Treat desktop and mobile nav as **two separate decisions**, not one — comparing a mobile bottom-tab pattern rendered at desktop width is meaningless.
- Render each candidate at its actual target viewport. `capture-screenshot.sh`'s `--viewport-size 1280,800` default is desktop-only; pass a mobile size explicitly for the mobile decision, e.g. `capture-screenshot.sh <url> <out.png> --viewport-size 375,667` — the later flag correctly overrides the script's hardcoded default (verified).
- For the mobile hamburger candidate, render the drawer in its **open** state, not closed — a closed hamburger icon shows nothing to compare against the bottom-tabs candidate's always-visible items.
- Variants: 2 per decision.
- Pattern: `.cards` grid for the picker screen, one decision at a time (or as two parallel decisions per the multi-decision pattern in `SKILL.md`); use [templates/mockups/nav-pattern-desktop.html.tmpl](../scripts/templates/mockups/nav-pattern-desktop.html.tmpl) and [templates/mockups/nav-pattern-mobile.html.tmpl](../scripts/templates/mockups/nav-pattern-mobile.html.tmpl) for each candidate's content. Verified: both render correctly and structurally distinct at their real target viewports.

### Content density (compact vs. comfortable spacing)
- Render a data-dense view — a table or list with enough rows that the cumulative effect of row height/padding is visible. Density differences are invisible on sparse content.
- Variants: 2-3 (compact, comfortable, spacious).
- Pattern: `.split` — density comparisons read best side-by-side since you're judging vertical rhythm directly.

### Dark/light mode default treatment
- Render the same representative screen with real content in both modes — the real question is usually contrast/legibility in the surface hierarchy, not aesthetic preference alone.
- Variants: 2 (occasionally 3, with "auto/system").
- Pattern: `.split` — direct side-by-side is the natural framing for light vs. dark.
