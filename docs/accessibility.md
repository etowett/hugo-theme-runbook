# Accessibility statement

**Applies to:** the Runbook Hugo theme, `main` as of 2026-07-28 (pre-release, no tagged version).
**Conformance target:** WCAG 2.2 Level AA.
**Required by:** [007 §4](../specs/007-verification.md).

> **This is a statement of target and evidence, not a claim of conformance.**
> Runbook is built *against* WCAG 2.2 AA and a substantial part of that target is verified
> mechanically on every pull request. A meaningful part of it is **not verified at all yet**, and
> §3 lists every one of those gaps by name. Nothing here should be read as a conformance
> certification, a VPAT, or an ACR.

> **No automated score is presented as conformance.** A perfect automated accessibility score means
> a tool found no violation among the subset of criteria it can test; roughly a third of WCAG is not
> machine-testable at all. Runbook currently has **no automated accessibility score to report** —
> the Lighthouse configuration in `.github/lighthouse/lighthouserc.json` is scaffolded and is not
> wired to a workflow ([verification §8](verification.md#8-what-is-implemented-what-is-a-placeholder)).
> When it is, it will be reported as an automated score and described as nothing more.

A theme is also only half of the answer. **Conformance is a property of a published site**, and a
site built with Runbook can still fail on content the theme never sees: missing `alt` text, a
heading level skipped in Markdown, a link labelled "here", a colour override that breaks contrast, or
anything injected through the [override hooks](extending.md). §5 lists what stays with you.

---

## 1. What is verified, and how

### 1.1 Colour and contrast — mechanically, on every pull request

[`scripts/check_contrast.py`](../scripts/check_contrast.py) parses the palette declarations out of
the stylesheets, resolves `var()` indirection, and asserts every foreground/background pair a reader
can actually end up looking at, **in both themes independently**.

**150 assertions across the two themes. All pass.** Run it yourself with
`python3 scripts/check_contrast.py -v` — it prints every ratio.

It goes past the usual token-versus-background sweep in three ways that matter for a code-first
theme:

- **Every syntax token is checked against every background that can slide underneath it** — the code
  background, the `{hl_lines=…}` band, and the diff insert/delete bands. A token that clears 4.5:1 on
  `--rb-code-bg` and fails on `--rb-code-hl-bg` is the normal outcome of tuning against one
  background, and nothing else catches it.
- **Non-text pairs are asserted at their own 3:1 threshold** (WCAG 1.4.11, not 1.4.3): focus rings on
  the page, on subtle surfaces and inside a code block; control boundaries; the highlighted-line
  marker.
- **Colour is checked as a signal, not only as contrast.** Deuteranopia and protanopia are simulated
  (Viénot/Brettel/Mollon) over the token pairs that genuinely co-occur — the pair list was produced
  by running ten languages through Chroma and recording which classes actually come out of the same
  block — and each pair must survive as hue separation (CIELAB ΔE76 ≥ 12) or fall back on lightness
  separation (≥ 1.50:1), the channel dichromats keep. This rejected two drafts of the palette for
  defects a trichromatic reviewer cannot see: a teal string and a grey comment that simulated to
  ΔE 2.8 under deuteranopia, and crimson keywords against grey operators that collapsed to ΔE 2.4
  under protanopia.

Measured headroom, so the margin is visible rather than asserted. Against the 4.5:1 text floor, the
weakest pair in **either** theme is **4.55:1** (muted text on a subtle surface); the weakest syntax
token is the comment at **6.54:1** light / **6.20:1** dark on the plain code background, falling to
**4.58:1** once a `{hl_lines=…}` band slides underneath it. Against the 3:1 non-text floor the
weakest pair is **3.13:1** (a control boundary on a subtle surface). Representative light-theme
values: body text 17.96:1, metadata 5.92:1, links 6.92:1, line numbers 4.98:1, copy/wrap control at
rest 5.50:1, focus ring 6.92:1, highlighted-line marker 3.39:1.

The check also asserts that the `<meta name="theme-color">` literals in
`_partials/head/theme-guard.html` still match `--rb-color-bg` in both themes, so the one value in the
design system that cannot read a custom property cannot silently drift.

**One deliberate non-WCAG number, labelled as such.** The `{hl_lines=…}` tint and the diff bands are
asserted at a **1.35:1 perceptibility floor**, which is *not* a WCAG threshold and is not presented
as one. WCAG's ratio is a luminance ratio and is the wrong instrument for two *backgrounds*:
near-black luminances are compressed enough that visibly distinct dark bands score around 1.1:1. A
tint deep enough to clear 3:1 on its own would push half the syntax palette below 4.5:1 once it slid
underneath. So the WCAG 1.4.11 signal for a highlighted line is a **3:1 inline-start marker**
(measured 3.39:1) and the tint only reinforces it.

### 1.2 The code block, driven in a browser

The code block is the theme's primary object and the only component with meaningful interactive
behaviour, so it was driven in **headless Chrome at 360, 768 and 1280 px, with and without script
execution** (PR
[#9](https://github.com/etowett/hugo-theme-runbook/pull/9)). Asserted, not eyeballed:

- `tabindex="0"` lands on exactly the blocks that actually scroll and nowhere else, and is removed
  again when a block is wrapped. Chroma emits `<pre tabindex="0">` on every block unconditionally;
  Runbook strips it and re-adds it by measurement, so a page with 158 blocks does not cost 158 tab
  stops.
- Zero chrome-over-glyph overlap at all three widths, including scrolled fully to the end.
- The copy confirmation is announced through an `aria-live="polite" role="status"` region, created
  once per page and positioned off-screen.
- Copy payloads asserted directly: `{prompt="$"}` filtering drops output lines and keeps
  `\`-continuations, a block without `{prompt=}` copies verbatim, and the line-number gutter is a
  separate `<td>`, is `user-select: none`, and is outside the copied element.
- Indented `pre > code` — which bypasses the render hook in every Hugo version — matches the enhanced
  case property for property.
- **Scripting disabled:** 16 controls present in the DOM, 16 of them `hidden`, 0 `tabindex`, 0 live
  regions. Nothing is announced that cannot be operated, and no code is hidden or broken.

### 1.3 Structural properties, verified by reading the built output

These are asserted in the templates and visible in `hugo --source exampleSite … --panicOnWarning`
output on every pull request:

| | |
|---|---|
| Skip link | First focusable element, `href="#rb-main"`, moves on `:focus` from off-screen into view |
| Language and direction | `<html lang>` from `site.Language.Lang`, `dir` from a per-language param — accessors that are stable across the whole supported Hugo range |
| Headings | `render-heading.html` emits stable ids and an anchor with a real accessible name (`aria-label`), not a bare `#` |
| Landmarks | `main`, `nav` (`aria-labelledby`/`aria-label`), `header`, `footer`; current nav item carries `aria-current` |
| Controls | Wrap toggle carries `aria-pressed`; copy and wrap carry `aria-label` **and** `title` |
| Target size (WCAG 2.2 **2.5.8**) | `--rb-target-min: 24px` applied to the code controls and to the theme toggle |
| Focus visibility | A single `:focus-visible` rule — 2px outline, 2px offset — on every interactive element, contrast-gated in both themes |
| Focus not obscured (WCAG 2.2 **2.4.11**) | The stylesheets contain **no `position: sticky` and no `position: fixed`** rule at all, so no element scrolls over a focused control. This is read from the CSS, not from a manual test |
| Reduced motion | Every transition in the theme sits inside a `@media (prefers-reduced-motion: reduce)` guard that collapses animation, transition **and** `scroll-behavior` |
| Text | Every UI string comes from `i18n/en.yaml`; no user-visible string is hard-coded in a template |
| New-tab warning (WCAG **3.2.5**) | `target="_blank"` is off by default. When `externalLinksNewTab` turns it on, the link also gains a visually hidden "(opens in a new tab)" — the behaviour is announced rather than sprung |
| Zero-JavaScript | The table of contents is ordinary same-document anchors; scroll-spy is an enhancement. Copy and wrap controls ship `hidden` and are unhidden only when they can work. The `details` shortcode is native `<details>` |

### 1.4 Deliberate design decisions with an accessibility rationale

- **Long lines scroll; they never soft-wrap by default.** Wrapping a command silently changes what
  the reader believes the command to be. The wrap toggle exists so a reader who needs reflow can ask
  for it per block, and it appears only on blocks that overflow.
- **The bundled code font is a correctness decision.** 44% of the reference archive draws box-drawing
  glyphs (`└ ├ ─ ●`). Without coverage, a fallback face substitutes *mid-block* at a different
  advance width and column alignment in captured terminal output breaks. `bundledCodeFont = false`
  falls back to the system stack for anyone who prefers it.
- **No saturated syntax token sits within 25° of the accent hue**, and the contrast gate enforces it.
  Blue on the reading surface means "you can focus or click this" and nothing else — which matters
  most inside a code block, where a focused copy button would otherwise compete with a blue keyword
  directly beneath it.

---

## 2. Standards and how to read the target

- **WCAG 2.2, Level AA** is the target for the theme's own markup, CSS and JavaScript.
- Level AAA is **not** targeted. Some AAA criteria (for example 1.4.6 Contrast Enhanced at 7:1) are
  met incidentally by parts of the palette; that is not a claim about the whole.
- Criteria that are **not applicable** to a theme that ships no forms, no media, no timing and no
  authentication: 1.2.x (time-based media), 2.2.x (timing), 2.5.7 (dragging movements), 3.3.7–3.3.9
  (redundant entry, accessible authentication). A consuming site that adds a comment widget or a
  contact form through the [override hooks](extending.md) takes those on itself.

---

## 3. Known limitations — what has **not** been tested

This is the part of the document that does the work. Everything below is untested rather than
known-broken; **untested is not the same as passing**, and none of it should be assumed to work.

### 3.1 Not tested with any screen reader

**No screen reader has been run against Runbook at all** — not VoiceOver, not NVDA, not JAWS, not
Orca, not TalkBack. Everything in §1.3 is an assertion about *markup*, and correct markup is a
necessary but not sufficient condition for a usable screen-reader experience. In particular these
are unverified in practice:

- how the `aria-live` copy confirmation is actually announced, and whether it interrupts;
- whether a 158-block page is navigable by rotor or by heading;
- whether the corner language tag and the two icon-only controls read sensibly in sequence at the top
  of each block;
- whether the code block's focusable scroll container is announced usefully when it takes focus.

[007 §3.6](../specs/007-verification.md) lists "VoiceOver on an article page" as a release checklist
item. It has not been done.

### 3.2 Not tested on touch, and not tested on Safari

iOS Safari touch interaction is **manual-only by design** ([007 §3.6](../specs/007-verification.md))
and has not been performed. Desktop Safari has not been tested either. This is a real gap for the
copy button specifically: `navigator.clipboard.writeText` has platform-specific user-activation
rules, and Runbook's touch styling deliberately diverges — under `(hover: none), (pointer: coarse)`
the controls are always visible rather than revealed on hover, and that branch has not been exercised
on a real device.

### 3.3 Not tested under Windows High Contrast / forced colours

No `@media (forced-colors: active)` handling exists in the stylesheets and no testing has been done.
Two specific risks are unmitigated:

- the copy, copied and wrap icons are **`mask-image` pseudo-elements painted with `currentColor`**,
  not inline SVG. Forced-colors mode may drop the mask, in which case the button paints a solid
  square — visible and operable, but not meaningful;
- the `{hl_lines=…}` band and the diff bands are backgrounds, and forced-colors mode overrides
  backgrounds. The 3:1 inline-start marker (§1.1) is a border and should survive, but this is
  reasoning, not a measurement.

### 3.4 Not tested at 200% zoom, and reflow is unverified

WCAG 2.2 **1.4.4 Resize Text** and **1.4.10 Reflow** have not been tested. The layout is built with
logical properties and relative units and the code block is an explicit horizontal scroll container —
which 1.4.10 permits, since the code is content that requires two-dimensional layout — but *"we used
`rem`"* is not a test result.

### 3.5 The clipboard was never touched

Copy was verified by asserting the **payload the handler constructs**, in headless Chrome. It has
never been checked against a real operating-system clipboard, in a real browser, with a real
permission prompt. Specifically untested:

- the `document.execCommand('copy')` fallback path, which triggers only on an insecure origin or a
  denied Clipboard-API permission. That is **browser state, not page content**, so it cannot be a
  content fixture; it belongs to the Playwright suite, which is
  [scaffolded and has no baselines](verification.md#7-visual-regression-and-the-golden-update-workflow);
- the final degradation — a copy attempt where *both* paths fail, the button announces the failure and
  then hides itself;
- whether what lands on the clipboard matches what was measured, on any platform.

### 3.6 Keyboard-only navigation of the whole page

Keyboard behaviour was asserted *for the code block* (§1.2). A manual keyboard-only pass over a whole
article — skip link, header navigation, theme toggle, table of contents, pagination, footer, in tab
order, in both themes — has **not** been performed. It is a release checklist item in
[007 §3.6](../specs/007-verification.md).

### 3.7 Everything else on the manual matrix

From [007 §3.6](../specs/007-verification.md), none of these has been done:

| Item | State |
|---|---|
| Keyboard-only navigation (whole page) | not done — §3.6 |
| VoiceOver on an article page | not done — §3.1 |
| Touch interaction on iOS Safari | not done — §3.2 |
| 200% zoom and reflow | not done — §3.4 |
| Windows High Contrast | not done — §3.3 |
| `prefers-reduced-motion` | implemented in CSS, **not manually verified** |
| Theme switching with `localStorage` disabled | implemented (`try`/`catch` on every access), **not manually verified** |
| Print / save-as-PDF | `assets/css/print.css` ships, **not manually verified** |
| Safari and iOS Safari (manual half of the browser matrix) | not done |

### 3.8 Automated gates that are not running yet

- **Lighthouse** — configuration pinned, not wired to a workflow. No score exists.
- **Visual regression** — Playwright configuration pinned (3 viewports × 2 themes), **no baselines
  committed**, deliberately, until the visual freeze.
- **Zero-JS, storage-disabled and strict-CSP passes** — specified, not started; they land with the
  Playwright suite.

### 3.9 No third-party audit

Runbook has had **no external accessibility audit and no evaluation by disabled users**. Everything
in §1 was produced by the same people who wrote the code.

### 3.10 The theme is pre-release and the layout is still moving

Search, shortcodes and several list-view refinements are in flight, and the table of contents is not
yet styled. Anything in §1 describes `main` as of the date at the top of this file.

---

## 4. If you find a barrier

Open an issue: <https://github.com/etowett/hugo-theme-runbook/issues>. Accessibility reports are
treated as bugs, not as feature requests. A concrete report — browser, assistive technology and
version, the page, and what you expected — is worth more than a scanner dump, and a scanner finding
without a reproduction may be a false positive.

A barrier that makes the theme unusable with an assistive technology is handled on the same footing
as a build break: see the
[version and support policy](../CHANGELOG.md#versioning-upgrades-and-deprecation).

---

## 5. What stays your responsibility

Runbook cannot make a site conformant on its own. As the site owner you still own:

- **`alt` text.** The image render hook passes the Markdown alt text straight through. `![](x.png)`
  produces `alt=""`, which is correct for a decorative image and wrong for every other kind.
- **Heading order.** The theme styles `h1`–`h6` and builds the table of contents from what is on the
  page. It does not renumber a skipped level.
- **Link text.** "Click here" is a content problem the theme cannot see.
- **Colour overrides.** `params.runbook.accent` and any `--rb-*` custom property you override are
  **not** re-checked by the contrast gate; that gate runs against the shipped palettes only. If you
  retheme, run `python3 scripts/check_contrast.py` against your values.
- **Anything injected through the [override hooks](extending.md)** — analytics, comment widgets,
  embeds. The theme ships no vendors and cannot vouch for one you add.
- **Language.** Set `languages.<code>` correctly, and `direction = "rtl"` where it applies, or
  `lang`/`dir` will be wrong on every page.
