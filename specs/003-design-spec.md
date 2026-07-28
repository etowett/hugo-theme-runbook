# 003 — Design specification

**Status:** specification
**Last revised:** 2026-07-28
**Evidence base:** [002 — Corpus profile](002-corpus-profile.md),
[004 — Hugo mechanics](004-hugo-mechanics.md)

---

Direction: **documentation-grade**. Sans-serif prose, generous measure, strong code presentation.
Reads as first-class technical documentation — calm and authoritative rather than novelty-retro, and
it ages well.

```
┌────────────────────────────────────────────┐
│ Runbook            Posts  Tags  About  ◐   │
├────────────────────────────────────────────┤
│  How to Install Redis 6 on Rocky Linux 8   │
│  Mar 4, 2026 · 6 min · Linux, Database     │
│                                            │
│  Redis is an in-memory data store used     │
│  as a cache, broker, and database.         │
│                                            │
│  Prerequisites                             │
│  ─────────────────────────────────────     │
│  You need a server with sudo access.       │
│                                            │
│  ╭ sh ───────────────────────────── copy ╮ │
│  │ sudo dnf -y install redis             │ │
│  ╰───────────────────────────────────────╯ │
└────────────────────────────────────────────┘
```

## 3.1 Typography

- **Prose:** system sans stack by default (`-apple-system, Segoe UI, Inter, …`) — zero network cost.
  Optional self-hosted variable Inter or Geist Sans, enabled by config.
- **Code:** self-hosted **JetBrains Mono**, subset WOFF2, `font-display: swap`. Variable weights,
  true italic, good cross-platform rendering. Ligatures **off** by default — they misrepresent shell
  operators (`>=`, `!=`, `->` in shell are not the glyphs a ligature draws); opt-in via config.
- Base size 17–18px. Prose measure **68–72ch**. Line height 1.65 prose / 1.5 code.
- **Inline code** carries real weight here (8,049 spans, 16.2 per post): subtle tinted background, no
  border, `font-size: 0.9em` to compensate for mono x-height. It must never break the prose baseline.

### REQ-FONT-1 — the subset must include box-drawing glyphs

**221 posts (44% of the archive) contain `└ ├ ─ ●` across 1,177 lines** — `systemctl status` trees,
`tree` output, `ss -tulpn` tables. A further 48 posts contain `→`.

A Latin-only subset renders those glyphs from the fallback font *mid-block*, producing mismatched
weight and broken box alignment in exactly the output readers scan most carefully.

The subset MUST include:

| Range | Block |
|---|---|
| U+2500–257F | Box Drawing |
| U+2580–259F | Block Elements |
| U+25A0–25FF | Geometric Shapes (`●`) |
| U+2190–21FF | Arrows |

Plus Latin-1 Supplement and General Punctuation. A `systemctl status` output fixture is added to the
visual-regression set ([007](007-verification.md)) specifically to catch subset regressions.

### REQ-FONT-2 — the font is optional and budgeted

The bundled font is a **capability, not a requirement**. A zero-byte system monospace stack
(`ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`) must remain fully supported and be the
fallback when the font is disabled. Font bytes count against their own budget
([005](005-performance-budgets.md) §3.1), not against CSS.

**Licensing verified:** JetBrains Mono is OFL-1.1 and declares **no Reserved Font Name**, so a
subset may legally retain the name.

## 3.2 Colour and themes

- Neutral grayscale foundation, **one** accent hue for links, focus rings and active states.
- Both themes independently meet **WCAG 2.2 AA**: 4.5:1 body text, 3:1 large text and UI components.
  Verified in CI ([007](007-verification.md)).
- **Every Chroma token contrast-checked individually in both themes.** This is where most themes
  fail. Comments are usually the worst offender. Reference:
  [`ericwbailey/a11y-syntax-highlighting`](https://github.com/ericwbailey/a11y-syntax-highlighting).
- **Tune the palette for shell first.** Chroma's Bash lexer emits a narrow token set — `nb`
  (builtin), `s`/`s1`/`s2` (strings), `c1` (comment), `nv` (variable), `o` (operator). Those carry
  roughly 80% of all coloured output in this corpus and are the tokens whose contrast matters most.
- Avoid red/green as the sole distinguishing signal (deuteranopia).
- Dark theme uses a near-black (`#0d1117`-ish), not pure black — reduces halation for astigmatic
  readers.
- **`<meta name="theme-color">`** synced to the active palette.

## 3.3 The code block

The differentiating feature. Implemented as `layouts/_markup/render-codeblock.html`
(see [004](004-hugo-mechanics.md) §3 for the path rationale).

### REQ-CB-1 — never forward the site's line-number config

**Restated from [004](004-hugo-mechanics.md) §2 because it is the single most important
implementation rule in this spec.**

The hook MUST build the option set it passes to `transform.Highlight` explicitly, with line numbers
forced off unless the individual block opted in. It MUST NOT forward the site's
`markup.highlight.lineNos` or `lineNumbersInTable`.

Site configuration is untrusted input to a distributable theme. Hugo merges theme config *underneath*
site config, so a theme default cannot win. citizix sets `lineNos: true, lineNumbersInTable: true`
today — that is what produces its 484-page line-number-table problem, and without this rule Runbook
would inherit it verbatim on day one.

### REQ-CB-2 — chrome is uniform, not threshold-switched

Issue #1 proposed: blocks of ≤2 lines get no header bar; blocks of 3+ get the full header.

**Rejected.** At the measured distribution, ≤2 lines is **57.0%** of blocks — the "exception"
treatment is the majority case. With a median of 16 blocks per post, a threshold rule produces a page
where chrome flickers on and off between adjacent blocks. It also introduces a magic number that has
already had to move once (the original rule was written against a 40.3% figure that is now 45.2%).

**Instead:**

- **No block gets a header bar by default.** Every block gets a muted corner language tag and a copy
  affordance.
- **The header bar appears only when there is something to put in it** — a `file=` attribute, or an
  author-supplied caption.
- Line numbers, when opted in, do not trigger a header.

This is simpler to implement, visually consistent at 18 blocks per post, satisfies the original
goal ("never let chrome exceed content height") by construction, and has no threshold to re-tune when
the corpus shifts again.

### REQ-CB-3 — copy must work on touch and by keyboard

The original spec's "hover/focus-revealed copy button" has **no trigger on coarse pointers**, and iOS
Safari is in the browser matrix — a self-contradiction.

- Copy button is **always present**, styled as a low-contrast ghost control that gains contrast on
  hover and focus.
- Under `@media (hover: none), (pointer: coarse)` it is rendered at full contrast permanently.
- `:focus-within` reveals it for keyboard users.
- Target size ≥ 24×24 px (§3.7).
- Reserve inline-end padding on the code element so the button never covers code.

### REQ-CB-4 — copy semantics

- Copy the code element's `textContent`. **Do not duplicate code into a `data-` attribute** — at
  9,046 blocks that would roughly double code bytes in the HTML and blow the page-weight budget by
  itself.
- Normalise line endings to `\n`.
- Strip at most one structural trailing newline introduced by the fence.
- **Never heuristically strip `$ ` or `# `.** `#` may be a real shell comment; `$` may be data.
- Line-number gutters, when present, live in a separate element that is `user-select: none` and
  excluded from the copy.
- Provide an `aria-live` confirmation.
- Define a fallback when the Clipboard API is unavailable (insecure context, old browser): fall back
  to a selection-based copy, and if that fails, hide the button rather than presenting a broken one.

**Prompt handling.** 1,389 lines across 318 posts (64% of the archive) begin with `$ `. Mixed
command-and-output blocks are routine, so a naive copy button routinely copies output along with the
command. The resolution is an explicit per-block opt-in, never a heuristic — see
[006](006-architecture-decisions.md) Q2.

### REQ-CB-5 — horizontal scroll, never wrap by default

- `overflow-x: auto` on the pre. Wrapping is never the default.
- **1,586 blocks (17.5%) contain at least one line over 80 characters**; the longest single line is
  854 characters. Soft-wrapping a `kubeadm join` silently changes what the reader believes the
  command to be.
- A per-block **wrap toggle** with `aria-pressed`, **session-local and not persisted**. Wrapping is a
  property of the one long line being inspected, not a reading preference; persisting it would
  silently re-break the next command the reader copies by eye.
- Keep native scrollbars. An edge fade may supplement the scrollbar but must not be the only overflow
  affordance.
- Copy behaviour is independent of visual wrapping.

### REQ-CB-6 — keyboard scrolling without a tab-stop tax

Issue #1 mandated `tabindex="0"` on scrollable blocks. Two problems: overflow cannot be determined
from source (it depends on viewport and font metrics), and Chrome 127+ already makes scroll
containers keyboard-focusable by default — so unconditional `tabindex` adds a redundant tab stop per
block, which at 18 blocks per post is a real navigation tax.

Resolution: **apply `tabindex="0"` only to blocks that actually overflow**, measured client-side on
load and resize. Verify the behaviour in the keyboard pass ([007](007-verification.md)) rather than
hard-coding it.

### REQ-CB-7 — block attributes

Author-facing syntax, using **Hugo's canonical lowercase attribute names** so documentation matches
upstream examples:

| Attribute | Effect |
|---|---|
| ` ```bash {linenos=true} ` | Opt in to line numbers for this block |
| ` ```bash {hl_lines="2-4"} ` | Highlight lines — for the 3.5% of blocks over 30 lines |
| ` ```yaml {file="docker-compose.yml"} ` | Filename label; triggers the header bar |
| ` ```console {prompt="$"} ` | Prompt-aware copy — see [006](006-architecture-decisions.md) Q2 |
| ` ```text {output=true} ` | Command-output treatment — see [006](006-architecture-decisions.md) Q3 |

Chroma-known keys arrive in `.Options`; unknown keys in `.Attributes`. The hook reads each from the
correct place ([004](004-hugo-mechanics.md) §1).

### REQ-CB-8 — bare `pre > code` is the styled base case

`pre > code` is styled as the base case; `.highlight` is the **enhanced** case that adds token
colour. The two must be visually identical apart from syntax colouring — same padding, radius,
background, font and overflow behaviour.

This costs roughly 200 bytes of CSS and protects consumers who have `guessSyntax: false`, indented
code, or `markup.highlight.codeFences: false`. Indented code blocks bypass the render hook in every
Hugo version, so CSS is the only tool available for them.

**Do not ship `.wp-block-code` / `.wp-block-preformatted` styling.** Issue #1 proposed this as a
selling point. The reference archive now contains zero instances, `goldmark.renderer.unsafe: false`
escapes such markup anyway, and it is no longer a demonstrable claim. Offer it as a documented CSS
snippet in the migration guide, not as shipped bytes.

## 3.4 Layouts and navigation

- **List views are text-first.** Title, date, reading time, category, description. No image slot, no
  reserved aspect-ratio box. Cover images are supported for consumers who have them, never assumed.
- **Sticky TOC**, H2–H3 by default (H4 opt-in). Justified by heading volume — 3,250 H2 and 2,097 H3,
  93.7% of all headings — and by p90 = 30 code blocks per post.
  - **Scroll-spy is an enhancement, not a prerequisite.** Ship a static anchor TOC first; add active-
    state tracking only if its JS cost fits the budget.
- **Related posts** as a footer component. Hugo-native, zero JS, driven by the consumer's `related`
  config.
  - The original justification — "at 0.6 internal links per post this is the primary discovery path"
    — is **void**. The archive now averages 4.39 internal links per post and cross-references itself
    well. Related posts remain useful; they are not a design driver.
  - Define a maximum result count and an empty-result fallback. Test relevance manually against
    citizix's actual weighting (tags 100, categories 200, threshold 60).
- **Series support** via a `series` taxonomy with prev/next. Note that **themes cannot register
  taxonomies** — the consumer must add it to site config, so this ships with documentation or it
  does not work.
- **Real taxonomy browse pages** — grouped, counted, alphabetised. Not a tag cloud: 159 of 312 tags
  are used exactly once, so a cloud is mostly noise. Needs a low-usage grouping strategy.
- **Client-side search** over a build-time **metadata-only** JSON index
  ([005](005-performance-budgets.md) §4). No external service.
- Archive page grouped by year.
- **Main sections** must use Hugo's configurable `mainSections`, never a hard-coded `post`.

## 3.5 Shortcodes

- `admonition` / callout — note, tip, warning, danger, caution.
- **`tabs`** — one procedure, tabs per distro (`apt` / `dnf` / `zypper`). Note the honest scope: the
  "install X on Y" family is **46 posts, 9.3% of the archive**, not the "archive is full of" claimed
  in issue #1. Build it for future authoring, not to retrofit 46 posts. **All panels must be exposed
  without JS.**
- `details` — collapsible long output. Use native `<details>`; zero JS.
- `filetree` — directory structures.

Render hooks: `render-codeblock` (§3.3), `render-link` (external `rel="noopener"` + indicator),
`render-image` (lazy, width/height to prevent CLS), `render-heading` (anchor links).

> Usage reality check: the reference archive uses the existing `admonition` shortcode in **exactly
> one post**, and uses `tabs`, `details` and `filetree` **zero times**. These are authoring
> affordances for future content, and they must not block the core theme.

## 3.6 Accessibility

Skip-to-content link · visible `:focus-visible` rings · semantic landmarks · keyboard-operable
copy/toggle/tabs with `aria-live` · `prefers-reduced-motion` honoured · correct heading order, with
the theme emitting exactly one `<h1>` per page · `lang` **and `dir`** attributes · SVG icons with
accessible names · target size ≥ 24×24 px.

> The "must not emit a second `<h1>`" rule stands, but its stated reason ("59 posts already carry a
> body H1") is stale — that count is now **0**. Keep the rule for third-party consumers whose content
> may contain body H1s.

## 3.7 SEO

JSON-LD `Article` + `BreadcrumbList` · OG + Twitter card with per-page image fallback · canonical
URLs · full-content RSS · clean sitemap · per-page `robots` control · `lastmod` surfaced in markup.

Three specific requirements:

1. **Do not emit `articleBody` in JSON-LD.** citizix's current
   `layouts/partials/head/schema.html:52` emits `{{ $.Plain | jsonify }}`, duplicating the entire
   article as structured data. It costs more gzipped bytes than every line-number table on the page
   combined ([005](005-performance-budgets.md) §2), and provides no verified SEO benefit.
2. **Map page kinds to schema types explicitly.** `Article` must not be emitted for every `.IsPage`.
3. **Degrade cleanly when `lastmod` is absent.** Coverage is now 90.1%, up from 27.6% — but never
   print "Invalid date" on the remaining 49 posts.

## 3.8 Internationalisation

All UI chrome strings ("Copy", "Copied", "Table of contents", "Related", "On this page", date
formats) must come from `i18n/en.yaml`. RTL must be supported via the `dir` attribute — citizix's
current `baseof.html` already emits `dir`, and Runbook must not regress it.

This is a showcase-adoption requirement, not a citizix requirement, and it was absent from issue #1
entirely.
