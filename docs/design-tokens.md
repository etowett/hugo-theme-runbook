# Design tokens

**Status:** in force
**Owner:** the design-system workstream
**Gate:** `python3 scripts/check_contrast.py` — 156 assertions, both themes, must exit 0

The token **names** are frozen ([contracts §2.1](contracts.md#21-css-custom-properties)); the values
live in [`assets/css/tokens.css`](../assets/css/tokens.css) and the syntax palettes in
[`chroma-light.css`](../assets/css/chroma-light.css) / [`chroma-dark.css`](../assets/css/chroma-dark.css).

This document closes the two decisions [006](../specs/006-architecture-decisions.md#decisions-still-open)
left open for M1, and records how the numbers were arrived at rather than only what they are.

---

## 1. What is actually being designed for

Two measurements from [002](../specs/002-corpus-profile.md) drive nearly every value below, and
they are unusual enough that a general-purpose palette gets them wrong:

- **79% of the corpus is shell** — 7,143 of 9,046 blocks.
- **45.2% of all blocks are exactly one line**, 57.0% are two or fewer.

Running representative shell through Chroma's Bash lexer gives the real token frequency:

| Token | Count | Token | Count |
|---|---|---|---|
| `.s2` double-quoted string | 14 | `.o` operator | 7 |
| `.nv` variable | 9 | `.si` `${…}` interpolation | 4 |
| `.nb` builtin | 9 | `.m` number | 4 |
| `.k` keyword | 8 | `.c1` comment | 2 |

The finding that changed the design, though, is what emits **no token at all**: `sudo`, `dnf`,
`systemctl`, `grep`, `curl`, `mv`. The commands a runbook is made of are plain `Text`. So the
most-read glyphs in a shell block render in `--rb-code-text`, and the palette's job is to stay
quiet around them. That is why `.n` and `.nx` (bare identifiers, which in Python and SQL would
otherwise colour every variable name) are left uncoloured too.

---

## 2. The accent, the plate, and both palettes

### The ground is warm and the code plate is dark in BOTH themes

This is the decision everything else in the palette follows from, and it is the corpus
profile drawn rather than a mood.

[002](../specs/002-corpus-profile.md) counts 9,046 fenced blocks, **zero** Markdown body images
and **one** cover image across 497 posts. A theme for that content has exactly one picture on the
page and it is the code. So the plate is the darkest, most saturated object on the page in the
light theme too — `#211f1b` on a `#f5ead8` cream — instead of the barely-tinted rectangle it used
to be. The ground went warm for the same reason: a near-black plate on a neutral `#ffffff` page
reads as cold and as a hole; on cream it reads as an object.

`scripts/check_contrast.py` resolves the plate from `--rb-code-bg`, so this made the gate start
asserting the **light** theme's syntax palette against a **dark** plate, with no change to the
gate. That is the whole safety story for this change and it is why the palette below is a
light-on-dark one in both themes.

**The plate is `#211f1b` and not the `#2e2b25` the source design drew.** One step deeper, for a
measured reason: at `#2e2b25` there is no palette that simultaneously clears 4.5:1 on the
highlight band, clears 4.5:1 on the plate, and keeps every co-occurring token pair separable after
deuteranopia. The band's floor and the plate's floor close on each other and leave under 1.5:1 of
lightness to distribute across eight roles — see §3 for why lightness is the escape hatch that
matters. Three hand-tuned palettes each failed one pair before the constraint was recognised as
arithmetic rather than taste.

### The accent is terracotta, hue ≈ 25°

`--rb-color-accent` is `#8c491a` in light and `#f6a06b` in dark. This re-closes open decision #1,
which M1 closed on azure. The three reasons azure won then are worth restating, because two of
them still hold and the one that changed is the interesting one:

1. **Convention.** Blue is the hue a reader decodes as "link" without the underline doing the
   work. But Runbook underlines every link anyway, and `text-decoration` — not hue — is what
   WCAG 1.4.1 accepts as the non-colour signal. The convention was redundancy, not the affordance,
   so it is affordable to spend.
2. **Luminance range.** Unchanged as a requirement, and terracotta meets it: `#8c491a` is 5.72:1
   as text on the cream and `#f6a06b` is 7.96:1 on the warm ink, at one hue.
3. **It is the one hue family the syntax palettes do not use.** Still true — the reservation moved
   rather than lapsed.

**The cost, stated plainly.** Reserving 25° ± 25° took amber and red away from the syntax palette.
`--rb-syn-variable` — the shell `$FOO`, the corpus's third-commonest token — lost the obvious
colour for it and is now the one gold the guard still permits, at 57°. `--rb-syn-error` moved from
red to rose at 353°, which is why the wavy underline in the class map matters more than it did.

### `--rb-color-focus` is no longer an alias of the accent in the light theme

The focus ring has to clear 3:1 against the cream page **and** against the dark plate, because a
focused copy button sits on the plate. Solving both at once puts the ring in a narrow luminance
window; `#8c491a`, tuned for 4.5:1 as *text* on cream, is only 2.07:1 on the plate. `accent-600`
`#b2622d` satisfies both — 3.77:1 on the page, 3.35:1 on the tinted surface, 3.66:1 on the plate.
In the dark theme no such conflict exists and focus goes back to being the accent.

### `--rb-color-accent-2` — olive, and deliberately outside the reservation

`#56633f` / `#aebf92`. Structural, never interactive: the series rail, the `{output=true}` marker,
the blockquote rule. It is held at 4.5:1 so it can carry small text as well as a rule, and it is
**not** part of the 25° guard, because it never means "click this" and so never competes with
syntax colour for that meaning.

### Method — the palette was solved, not picked

The eight syntax values below were produced by search, not by hand. The constraint set is:

- ≥ 4.5:1 on `--rb-code-bg` **and** `--rb-code-hl-bg` in both themes, and on the diff bands for
  the two roles that land on them;
- every co-occurring pair separated by hue-after-dichromacy **or** by lightness (§3);
- ≥ 25° clear of the accent hue for anything with HSL S ≥ 0.25;
- comments the most recessive token, but never below AA.

That has no obvious closed form, and three successive hand-tuned attempts each failed exactly one
pair. The search uses the same arithmetic `scripts/check_contrast.py` runs, so the gate is the
oracle rather than a rubber stamp — reproduce any number below with
`python3 scripts/check_contrast.py -v`.

### The syntax palette — ONE set of values, both themes

Because the plate is dark in both themes and the two plates differ by 0.006 in relative luminance,
the same eight foregrounds clear their targets on both. They are declared once, unscoped, in
`chroma-light.css`. `chroma-dark.css` carries only the two diff bands, which can go deeper against
the darker plate. The gate still checks both themes independently.

| Role | Value | Hue | On plate (light) | On plate (dark) | On `hl-bg` (light) | Chroma classes |
|---|---|--:|--:|--:|--:|---|
| code text | `#f5ead8` | — | 13.82:1 | 15.31:1 | — | *(untokenised — commands)* |
| `--rb-syn-comment` | `#afa18c` | 36° | 6.50:1 | 7.20:1 | 4.72:1 | `c ch cm c1 cs cp cpf sd gp` |
| `--rb-syn-punct` | `#c5beb3` | 37° | 8.92:1 | 9.88:1 | 6.48:1 | `o p` |
| `--rb-syn-literal` | `#31cdc4` | 177° | 8.35:1 | 9.25:1 | 6.06:1 | `s sa sb sc dl s2 se sh si sx sr s1 ss l m mb mf mh mi il mo` |
| `--rb-syn-builtin` | `#c58ff0` | 273° | 6.71:1 | 7.43:1 | 4.87:1 | `nb bp nf fm nc nn` |
| `--rb-syn-variable` | `#c3bc45` | 57° | 8.30:1 | 9.20:1 | 6.03:1 | `nv vc vg vi vm` |
| `--rb-syn-keyword` | `#ea95b1` | 340° | 7.39:1 | 8.18:1 | 5.37:1 | `k kc kd kn kp kr kt ow or gd` |
| `--rb-syn-name` | `#5ace66` | 126° | 8.19:1 | 9.07:1 | 5.95:1 | `na nt nl no ni nd gi` |
| `--rb-syn-error` | `#fb7c8a` | 353° | 6.54:1 | 7.25:1 | 4.75:1 | `err gr gt` |

Measured clearances from the 25° accent: `error` **32°**, `variable` **32°**, `keyword` 45°,
`name` 101°, `builtin` 112°, `literal` 152°. The two greys sit at HSL S 0.13–0.18 and carry no hue
signal at all, so the guard exempts them.

### The page palette

| Token | Light | On page | On tinted surface | Dark | On page |
|---|---|--:|--:|---|--:|
| `--rb-color-text` | `#201e1d` | 13.95:1 | 12.40:1 | `#f5ead8` | 13.82:1 |
| `--rb-color-text-muted` | `#645c50` | 5.53:1 | 4.92:1 | `#c0b6a5` | 8.21:1 |
| `--rb-color-text-subtle` | `#675e51` | 5.35:1 | 4.76:1 | `#a19786` | 5.71:1 |
| `--rb-color-accent` | `#8c491a` | 5.72:1 | 5.09:1 | `#f6a06b` | 7.96:1 |
| `--rb-color-accent-hover` | `#643312` | 8.72:1 | 7.75:1 | `#ffc6a5` | 10.87:1 |
| `--rb-color-accent-2` | `#56633f` | 5.43:1 | 4.82:1 | `#aebf92` | 8.36:1 |
| `--rb-color-border-strong` | `#82796a` | 3.61:1 | 3.21:1 | `#82796a` | 3.83:1 |

`--rb-color-accent-contrast` (`#fff2eb` on the accent fill) is **6.21:1**. The design this comes
from filled its buttons with the base terracotta `#c67139` and set the label in `#fff2eb`, which
is **3.29:1** — a fail. The fix was the ramp step, not the hue: the design's own stylesheet
already set link *text* in `accent-700`, so only the *fill* had been drawn a step too light.

## 3. Colour as a signal, not just as contrast

[003 §3.2](../specs/003-design-spec.md#32-colour-and-themes) says avoid red/green as the *sole*
distinguishing signal. `check_contrast.py` makes that testable: it simulates deuteranopia and
protanopia (Viénot/Brettel/Mollon) and asserts that every co-occurring token pair is separated by
**hue after simulation, or by lightness (≥ 1.5:1 between the two)**. Failing both is the precise
definition of "distinguished by hue alone", and it is the failure a trichromatic reviewer cannot see.

Two design consequences fell straight out of the gate failing on the first draft:

- **Comments and strings collapsed.** A teal string and a grey comment at the same luminance
  simulate to dE 2.8 (light) and 1.6 (dark) — a dichromat literally cannot tell a comment from a
  string in a shell block. Fixed by pushing strings to 9.9:1 while comments hold at 6.5:1, so the
  pair is separated by lightness (1.51:1) rather than by a hue that is not there.
- **Punctuation and keywords collapsed under protanopia** (dE 2.4). Crimson simulates to a dark
  neutral, which is what the operator grey already is.

No palette of six hues keeps all six apart for a dichromat — the two cone-response axes collapse to
one. Pretending otherwise produces a gate nobody can pass, so lightness is an explicit, allowed
escape hatch: it is the channel dichromats keep.

The pair list is **measured, not assumed**. Representative bash, yaml, json, python, go, dockerfile,
sql, nginx and ini were run through Chroma and the classes that came out together were recorded.
`variable` (shell `$FOO`) and `name` (YAML/JSON keys) never share a block, so demanding they be
distinguishable would spend palette headroom on a case that does not exist.

`punct` is deliberately outside the set: operators are *structure*, not meaning, and are supposed to
read as a near-text grey.

Where red/green is unavoidable — diff `+`/`-` — it is never the only signal. The `+` and `-` are part
of the token text, and both lines additionally carry a background band.

---

## 4. Open decision #2 — the bundled font

**Decision: the bundled code font ships ON. The bundled prose font ships OFF, and does not exist.**

This matches the defaults already in the root `hugo.toml`
(`bundledCodeFont = true`, `bundledProseFont = false`).

### Why the code font is on

REQ-FONT-1 is the argument: **221 posts, 44% of the archive, draw `└ ├ ─ ●` across 1,177 lines** —
`systemctl status` trees, `tree` output, `ss -tulpn` tables. The system monospace stack does not
cover those glyphs consistently across platforms, and the failure mode is not "a different font",
it is a fallback face substituting **mid-block**, at a different advance width, which breaks column
alignment in exactly the captured output readers scan most carefully. That is a correctness problem
in the theme's primary content type, not a polish problem.

ADR-6's warning still holds — self-hosting is *not* automatically faster, and it buys transfer bytes.
The counter is that this is 25 KB, once, on a code-first theme, with `font-display: swap`.

### Why this does not violate the CLS = 0 gate

`font-display: swap` normally means a visible reflow. Here it does not move anything, by
construction:

- code line-height is `--rb-leading-code: 1.5`, a **unitless multiple of font-size**, so block
  height does not depend on the font's own metrics;
- `<pre>` does not wrap (REQ-CB-5), so a metric change alters the block's *scroll extent*, not its
  line count.

Nothing below the code block moves when the face swaps in. This is why the default is defensible
against the hard CLS = 0 assertion in [007 §3.3](../specs/007-verification.md#33-lighthouse--rewritten).

### The self-hosted display face and its fallback

The approved Citizix direction uses **Caprasimo** for the brand and headings. The original source
loaded it from `fonts.googleapis.com`, but success criterion 3 ([001 §5](../specs/001-overview.md))
rules out a third-party font request. Runbook now ships the Latin WOFF2 from the OFL release at
`static/fonts/caprasimo-latin.woff2` instead. It is 20,772 B raw, independently below the 30 KB
per-subset budget that `check_budgets.py` enforces; it does not consume the code font's budget.

`params.runbook.bundledDisplayFont` defaults to `true`. Set it to `false` to keep the same sizing
and geometry on the system sans fallback without downloading Caprasimo. A consumer can also replace
`--rb-font-display` from `custom-head.html`.

The geometry remains deliberate, including in the fallback:

| | Default-looking | Runbook |
|---|---|---|
| weight | 700 | **400** (`--rb-weight-normal`) |
| size, article `h1` | ~32px | **46px** (`--rb-text-4xl`) |
| size, home `h1` | ~40px | **52px** (`--rb-text-5xl`) |
| line-height | 1.2–1.3 | **1.05** (`--rb-leading-display`) |
| letter-spacing | 0 | **-0.015em** (`--rb-tracking-display`) |

All four survive the system stack intact. Caprasimo supplies the distinctive silhouette; the
geometry prevents the opt-out path from falling back to default browser heading proportions.

Below `h3` the tracking is switched back to `normal` and the weight to 500: at 19px a -0.015em
pull is a fifth of a pixel per glyph and reads as a rendering fault rather than as tight setting.

### Why the prose font is off, and absent

The prose failure mode does not exist — no glyph in the corpus's prose is missing from a system sans
stack. So it would be pure bytes. `params.runbook.bundledProseFont` is therefore a **reserved
no-op**: Runbook ships no prose face, and `head/theme-guard.html` deliberately has no branch for it,
because a branch would point `--rb-font-sans` at a family that does not exist. A consumer who wants
one adds the `@font-face` through the `custom-head.html` hook and overrides `--rb-font-sans`.

### Subset provenance

| | |
|---|---|
| Display source | [Caprasimo](https://github.com/google/fonts/tree/main/ofl/caprasimo), Latin WOFF2 from the Google Fonts release endpoint |
| Display licence | **OFL-1.1**. Text shipped at `static/fonts/Caprasimo-OFL.txt` |
| Display output | `static/fonts/caprasimo-latin.woff2` — **20,772 B**, against a ≤ 30 KB per-subset budget |
| Source | [JetBrains Mono v2.304](https://github.com/JetBrains/JetBrainsMono/releases/tag/v2.304), `fonts/variable/JetBrainsMono[wght].ttf` |
| Licence | **OFL-1.1, no Reserved Font Name** — a subset may legally keep the name. Text shipped at `static/fonts/OFL.txt` |
| Tool | `fonttools` 4.63.0 (`pyftsubset`), brotli for WOFF2 |
| Output | `static/fonts/jetbrains-mono-subset.woff2` — **25,032 B**, against a ≤ 30 KB budget |
| Axes | `wght` 100–800 variable — one file covers regular through bold, no second request |
| Glyphs | 464 |

Regenerate with:

```sh
pyftsubset 'JetBrainsMono[wght].ttf' \
  --unicodes='U+0020-007E,U+00A0-00FF,U+2000-206F,U+2190-21FF,U+2500-257F,U+2580-259F,U+25A0-25FF,U+2713-2717' \
  --layout-features='ccmp,locl' \
  --flavor=woff2 --no-hinting \
  --output-file=static/fonts/jetbrains-mono-subset.woff2
```

Coverage against REQ-FONT-1, verified from the built file's `cmap`:

| Range | Block | Covered |
|---|---|---|
| U+2500–257F | Box Drawing | 128/128 |
| U+2580–259F | Block Elements | 32/32 |
| U+25A0–25FF | Geometric Shapes (`●`) | 43/96 — every shape present in the corpus |
| U+2190–21FF | Arrows | 35/112 |
| U+0020–007E | Basic Latin | 95/95 |
| U+00A0–00FF | Latin-1 Supplement | 96/128 |
| U+2000–206F | General Punctuation | 32/112 |
| U+2713–2717 | ✓ ✗ | added beyond the spec — `systemctl`/`kubectl` output uses them |

The partial counts are not gaps: they are every codepoint JetBrains Mono itself defines in that
range. Nothing the spec requires is missing.

### `--layout-features='ccmp,locl'` — ligatures are removed, not disabled

Keeping `calt,liga` costs **17,300 B — 40% of the file** — to carry glyphs the theme deliberately
never draws, and it pushes the subset to 42,332 B, over budget. [003 §3.1](../specs/003-design-spec.md#31-typography)
is explicit that ligatures misrepresent shell operators: `>=`, `!=`, `->` in shell are not the glyphs
a ligature draws.

So they are dropped from the font, which makes "ligatures off" physical rather than
CSS-dependent — and drops the payload from 42 KB to 25 KB.

**Consequence to know about:** `params.runbook.codeFontLigatures = true` is a **no-op against the
shipped subset**. It still applies to the system stack and to a consumer who supplies their own full
JetBrains Mono build. To get ligatures on the bundled face, re-run the command above with
`--layout-features='calt,liga,kern,ccmp,locl,mark,mkmk'` and accept the 42 KB.

### Loading strategy

- `font-display: swap` — text is never invisible.
- **No `<link rel="preload">`**, deliberately. The face is discovered from a stylesheet that is
  already render-blocking and already in flight, and a preload would spend 25 KB on every page with
  no code block on it.
- The `src` URL is **relative** (`../fonts/…`), so it stays correct for a consumer serving from a
  subpath, which an absolute `/fonts/…` would break.
- Turning it off (`bundledCodeFont = false`) points `--rb-font-mono` at `--rb-font-mono-system`.
  Nothing then references the family, so the `@font-face` never triggers a download — the zero-byte
  fallback of REQ-FONT-2 is genuinely zero bytes.

> **Known limitation.** Hugo does not publish a theme's `static/` directory when the theme is
> reached through a **symlinked** `--themesDir` entry. Real install paths — submodule, release
> archive, Hugo Module — are all real directories and are unaffected. It only bites a local worktree
> that symlinks the theme into place, where the font 404s and the system stack takes over.

---

## 5. Theme switching and CSP

Three states on `<html data-theme>`: `auto`, `light`, `dark`, with CSS already correct for all three
before JavaScript runs. `head/theme-guard.html` only ever *changes* the answer.

`<meta name="theme-color">` is emitted server-side: media-scoped pairs for the `auto` default (the
zero-JS answer, and correct on its own), a single unconditional meta for an explicit light/dark
default. Neither can express "the reader chose dark on a light OS" — that is a stored preference —
so `js/modules/theme.js` collapses them into one resolved meta once it runs, reading the value back
out of the cascade with `getComputedStyle` rather than carrying a second copy of the token.

The literals in the template are the one value in the design system that can silently drift from the
palette, so `check_contrast.py` asserts they still match `--rb-color-bg` in both themes.

### CSP

The inline guard is the only inline script Runbook emits. Two options:

- **Nonce** — set `params.runbook.cspNonce`; it is emitted on the guard and on the font-override
  `<style>`. No coordination with a release.
- **Hash** — current value:

  ```
  script-src 'sha256-GytWXkQmO8lO9yfkf/nGk5uKoncvdhsJM4S8wnPhTUQ='
  ```

  Regenerate after any edit to the script text (the hash covers it byte for byte, whitespace
  included):

  ```sh
  python3 - <<'EOF'
  import re, hashlib, base64
  h = open('public/index.html').read()
  b = re.search(r'<script>(\(function\(\)\{try\{var t=localStorage.*?)</script>', h, re.S).group(1)
  print("'sha256-" + base64.b64encode(hashlib.sha256(b.encode()).digest()).decode() + "'")
  EOF
  ```

---

## 6. The token inventory

Contrast-critical pairs are the ones `check_contrast.py` asserts; everything else is layout or type.

### Surfaces and text

| Token | Purpose | Gated at |
|---|---|---|
| `--rb-color-bg` · `--rb-color-bg-subtle` · `--rb-color-surface` | page, tinted surface (table header, blockquote, inline code, pills), card | background |
| `--rb-color-text` | body copy | 4.5:1 on both surfaces |
| `--rb-color-text-muted` | metadata, TOC entries | 4.5:1 on both surfaces |
| `--rb-color-text-subtle` | decorative only — never load-bearing | 4.5:1 anyway |

Text values are tuned against `--rb-color-bg-subtle`, not `--rb-color-bg`, because muted text lands
in table headers and blockquotes. The white-background case is then true for free; the reverse is not.

### Lines — two tiers, and the difference is conformance, not looks

| Token | Purpose | Gated at |
|---|---|---|
| `--rb-color-border` | decorative separator: table cell, list rule, header underline | not gated — WCAG 1.4.11 does not reach it |
| `--rb-color-border-strong` | the visible **boundary of a UI component** — theme toggle, blockquote rule | **3:1** |

### Accent

| Token | Purpose | Gated at |
|---|---|---|
| `--rb-color-accent` | links, active state | 4.5:1 on both surfaces |
| `--rb-color-accent-hover` | link hover | 4.5:1 |
| `--rb-color-accent-contrast` | text **on** the accent (skip link, filled pill, brand) | 4.5:1 against the accent |
| `--rb-color-accent-2` | olive. Structural only — series rail, output marker, blockquote rule. **Outside** the 25° hue reservation | 4.5:1 on both page surfaces |
| `--rb-color-focus` | focus ring. **Not** an alias of the accent in the light theme — see §2 | **3:1** on page, subtle **and code** backgrounds |

### Code block

| Token | Purpose | Gated at |
|---|---|---|
| `--rb-code-bg` · `--rb-code-text` · `--rb-code-border` | the block | 4.5:1 |
| `--rb-code-chrome-fg` / `-hover` | copy and wrap controls at rest / hover | 4.5:1 |
| `--rb-code-gutter-fg` | line numbers | 4.5:1 |
| `--rb-code-output-bg` | `{output=true}` muted treatment (Q3) | code text 4.5:1 on it |
| `--rb-code-hl-bg` | `{hl_lines=…}` band | every token 4.5:1 **on it** |
| `--rb-code-hl-border` | `{hl_lines=…}` inline-start marker | **3:1** |

> `--rb-code-hl-border` **is now consumed.** `code.css` draws it as
> `box-shadow: inset 2px 0 0 0 var(--rb-code-hl-border)` on `.line.hl` — `box-shadow` and not
> `border-inline-start`, because a border on a `display: block` span inside a `<pre>` shifts that
> one line's text by its own width and breaks the column alignment the bundled font exists to
> protect. The conformant WCAG 1.4.11 signal for a highlighted line is therefore actually drawn,
> rather than being carried by the shallow tint alone.

#### Why the highlight band is shallow, and why that is correct

The tint is deliberately faint — 1.43:1 (light), 1.35:1 (dark) against `--rb-code-bg`. The binding
constraint runs the other way: **every syntax token has to keep 4.5:1 once that background slides
underneath it**, and a tint deep enough to clear 3:1 on its own would push half the palette below AA.

WCAG's ratio is also the wrong instrument for two *backgrounds*. It is a luminance ratio, and
near-black luminances are compressed enough that two visibly distinct dark bands score ~1.1:1. So
the 1.35 floor in the gate is labelled as a **perceptibility floor, explicitly not a WCAG claim**;
the conformant 1.4.11 signal is `--rb-code-hl-border` at 3:1.

### Table of contents

`--rb-toc-fg`, `--rb-toc-fg-active`, `--rb-toc-marker`, `--rb-toc-active-bg`, `--rb-toc-hover-bg`
— named TOC tokens, declared separately so the templates workstream has a stable seam to consume
and so every state the rail can be in is asserted.

**Both state fills are named, and that is the fix for a measured bug rather than tidiness.** The
rail and the mobile sheet are painted `--rb-color-surface`. Hover and the selected entry both
originally reached for `--rb-color-bg-subtle`, and `--rb-color-surface` and `--rb-color-bg-subtle`
are the *same* `#2a2722` in the dark palette by design — so both states resolved to a **1.00:1**
background change while every foreground assertion in the gate passed. A foreground-on-background
sweep structurally cannot see that, because the collapse is between two backgrounds.

| | light | dark | vs the `--rb-color-surface` card |
|---|---|---|---|
| `--rb-toc-hover-bg` | `--rb-color-bg-subtle` `#ebddc5` | `#3a352c` | 1.22:1 in **both** themes |
| `--rb-toc-active-bg` | `#eec7ab` | `--rb-color-accent` `#f6a06b` | 1.43:1 · 7.20:1 |
| `--rb-toc-fg-active` | `--rb-color-accent-hover` `#643312` | `--rb-color-accent-contrast` | 6.62:1 · 7.96:1 on the pill |

The light selected pill is the constrained end. It is squeezed from both sides — deep enough to
clear the **1.35 perceptibility floor** against the `#f9f4ed` card, shallow enough that the
selected ink keeps 4.5:1 on it. `#eec7ab` clears both at 1.43:1 and 6.62:1, and the ink is
accent-**800** rather than the accent-700 link colour precisely because accent-700 only reaches
4.34:1 on that pill. The dark palette inverts the relationship instead: a full accent fill with
its contrast ink, because no tint of a card can be distinguished from a card that shares its value.

Two of the six assertions are **background-against-background and are explicitly not WCAG
claims**, for the same reason the highlight band's floor is not — see [above](#why-the-highlight-band-is-shallow-and-why-that-is-correct).
A luminance ratio is a poor instrument for two backgrounds, but a sufficient one to catch a
collapse to 1.00:1. The selected pill is held at the existing `HL_BAND_MIN` 1.35; hover is held at
a lower `TOC_HOVER_MIN` 1.15, because hover is transient and is reinforced by a
muted→body text-colour change that the selected state does not rely on.

### Type, space, shape

`--rb-font-sans` / `--rb-font-mono` / **`--rb-font-display`** and the two `-system` variants;
`--rb-text-*` (base 17px, up to `-4xl` 46px and `-5xl` 52px), `--rb-leading-*` (including
**`--rb-leading-display`** 1.05), **`--rb-tracking-display`** -0.015em, `--rb-weight-*`;
`--rb-space-1..8` on a 4px base; `--rb-radius-sm|md|lg` **8 / 16 / 28px**, plus
**`--rb-radius-code`** 20px for the plate and **`--rb-radius-pill`** 999px for tags, nav, TOC
entries and archive rows; **`--rb-shadow-sm|md|lg`**, warm-tinted rather than neutral black
because a grey shadow on a cream ground reads as dirt; `--rb-measure` 70ch,
`--rb-content-width`, `--rb-page-width` **72rem**, `--rb-gutter`; `--rb-target-min` 24px and
**`--rb-target-touch`** 44px, `--rb-focus-width`, `--rb-focus-offset`; `--rb-transition`;
`--rb-z-header` / **`--rb-z-sheet`** / `--rb-z-skip`.

None of these are configuration. There is deliberately no `params.runbook.accent`, no radius
setting and no font-size setting: every one of them is a value the contrast gate or the budget
gate reasons about at build time, and a value from site config is a value neither gate can see.
Overriding the custom properties directly is the supported route, and §7 says what that costs.

---

## 7. What a consumer may override

**Safe to override** — this is the supported theming surface:

- any `--rb-color-*`, `--rb-code-*`, `--rb-syn-*` value;
- `--rb-font-sans`, `--rb-font-mono`, `--rb-measure`, `--rb-text-*`, `--rb-space-*`, `--rb-radius-*`.

The syntax palette is **11 custom properties per theme**, not a 60-selector fork. Retheming
Chroma means:

```css
:root { --rb-syn-literal: #0a5d55; }
:root[data-theme="dark"] { --rb-syn-literal: #4fd6c8; }
```

Do it from the `custom-head.html` hook (ADR-8), never by editing theme files.

**If you override a colour, re-run the gate.** `scripts/check_contrast.py` reads the theme's own
CSS, so it validates the shipped palette, not yours — an override is unverified until you check it.

**Internal, do not rely on:** `--rb-z-*`, `--rb-transition`, and the exact class-to-role mapping in
`chroma-light.css`. Roles are stable; which Chroma class belongs to which role may be re-tuned as the
corpus is re-measured.
