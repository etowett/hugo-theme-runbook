# Design tokens

**Status:** in force
**Owner:** the design-system workstream
**Gate:** `python3 scripts/check_contrast.py` — 150 assertions, both themes, must exit 0

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

## 2. Open decision #1 — the accent hue and both palettes

### The accent is azure, hue ≈ 212°

`--rb-color-accent` is `#0a58b0` in light and `#58a6ff` in dark. Three reasons, none of them taste:

1. **Convention.** Blue is the only hue a reader already decodes as "link" without the underline
   doing the work. Runbook underlines links anyway, so the convention is free redundancy.
2. **Luminance range.** The accent has to clear 4.5:1 as text on `#ffffff` *and* on `#161b22`,
   at the same hue, or the theme has two accents rather than one. Azure does: 6.92:1 and 6.85:1.
   Teal and green cannot without desaturating to grey at the dark end; orange cannot without
   going brown at the light end.
3. **It is the one hue family the syntax palettes do not use.**

### The accent hue is reserved for interaction

No saturated Chroma token in either palette sits within **25°** of 212°, and
`check_contrast.py` asserts it. The measured clearances are 35° (`.literal`), 55° (`.builtin`),
84° (`.name`), 127° (`.keyword`), 153° (`.error`), 178° (`.variable`).

The payoff: on the reading surface, blue means "you can click or focus this" and nothing else.
It matters most inside a code block, where a focused copy button sits directly on top of coloured
tokens — a place where a blue keyword and a blue focus ring would compete.

### Method — the palettes were solved, not picked

Both palettes were derived by searching contrast targets under the full constraint set rather than
chosen and then checked. The binding constraints:

- every token ≥ 4.5:1 on `--rb-code-bg` **and** on `--rb-code-hl-bg` and its diff band;
- every co-occurring pair separated by hue-after-dichromacy **or** by lightness (§3);
- comments the most recessive token, but never below AA.

The result is a palette that is high-contrast by construction — the weakest token in either theme
is the comment, at 6.54:1 (light) and 6.20:1 (dark), against a 4.5:1 floor.

### Light — `--rb-code-bg` `#f6f7f9`

| Role | Value | On code bg | On `hl-bg` | Chroma classes |
|---|---|---|---|---|
| code text | `#14171c` | 16.76:1 | — | *(untokenised — commands)* |
| `--rb-syn-comment` | `#515a64` | 6.54:1 | 4.58:1 | `c ch cm c1 cs cp cpf sd gp` |
| `--rb-syn-punct` | `#465160` | 7.52:1 | 5.27:1 | `o p` |
| `--rb-syn-literal` | `#014743` | 9.88:1 | 6.92:1 | `s sa sb sc dl s2 se sh si sx sr s1 ss l m mb mf mh mi il mo` |
| `--rb-syn-builtin` | `#5d22a6` | 8.73:1 | 6.12:1 | `nb bp nf fm nc nn` |
| `--rb-syn-variable` | `#7f4001` | 7.43:1 | 5.21:1 | `nv vc vg vi vm` |
| `--rb-syn-keyword` | `#760f33` | 10.39:1 | 7.28:1 | `k kc kd kn kp kr kt ow or gd` |
| `--rb-syn-name` | `#056011` | 7.29:1 | 5.11:1 | `na nt nl no ni nd gi` |
| `--rb-syn-error` | `#8e1a10` | 8.50:1 | 5.96:1 | `err gr gt` |

### Dark — `--rb-code-bg` `#161b22`

| Role | Value | On code bg | On `hl-bg` |
|---|---|---|---|
| code text | `#e6edf3` | 14.64:1 | — |
| `--rb-syn-comment` | `#8f9cad` | 6.20:1 | 4.58:1 |
| `--rb-syn-punct` | `#9facbc` | 7.50:1 | 5.54:1 |
| `--rb-syn-literal` | `#49d2c8` | 9.34:1 | 6.90:1 |
| `--rb-syn-builtin` | `#c296f9` | 7.43:1 | 5.50:1 |
| `--rb-syn-variable` | `#f48a0a` | 6.99:1 | 5.17:1 |
| `--rb-syn-keyword` | `#fba6c4` | 9.35:1 | 6.91:1 |
| `--rb-syn-name` | `#35b546` | 6.47:1 | 4.78:1 |
| `--rb-syn-error` | `#f88d83` | 7.52:1 | 5.56:1 |

Hue angles are **identical across themes** — a reader switching themes should not have to relearn
which colour means "string". Saturations are not: perceived chroma collapses on a dark background,
so holding the same nominal saturation reads as washed-out grey. Each hue was re-tuned to land on
its own contrast target.

One asymmetry is deliberate. `--rb-syn-variable` sits at 8.2:1 in dark against 6.6:1 in light, and
`--rb-syn-keyword` inverts with it. The amber/rose pair is the one a deuteranope compresses
hardest, and on a dark background the amber is the member that has to pull away.

### The cost, stated plainly

Holding comments at 6.5:1 is what buys a visible highlight band (§6), because the band's depth is
capped by the *weakest* token on it. But it also forces strings down to 9.9:1 to keep the 1.5:1
lightness separation from comments — and teal has its maximum chroma at mid lightness, so the light
theme's string colour lands at Lab C\* 20.7. That is a deep teal rather than a vivid one: above the
~20 threshold where a hue starts reading as grey, but not by much, and it is the least saturated
chromatic token in either palette.

Lightening comments to 5.5:1 would give a richer string colour and collapse the highlight band from
1.43:1 to roughly 1.20:1. The band is a functional affordance and the string colour is already
legible as teal, so the band won.

### Why comments are the token most themes fail

Because the instinct is to make comments recede with low **contrast**. This palette uses low
**chroma** instead: the comment grey is near-neutral (HSL S ≈ 0.11) and still clears 6.5:1. It
recedes because it has no colour, not because it is faint.

---

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

### Why the prose font is off, and absent

The prose failure mode does not exist — no glyph in the corpus's prose is missing from a system sans
stack. So it would be pure bytes. `params.runbook.bundledProseFont` is therefore a **reserved
no-op**: Runbook ships no prose face, and `head/theme-guard.html` deliberately has no branch for it,
because a branch would point `--rb-font-sans` at a family that does not exist. A consumer who wants
one adds the `@font-face` through the `custom-head.html` hook and overrides `--rb-font-sans`.

### Subset provenance

| | |
|---|---|
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
| `--rb-color-bg` · `--rb-color-bg-subtle` · `--rb-color-surface` | page, tinted surface (table header, blockquote, inline code), card | background |
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
| `--rb-color-accent-contrast` | text **on** the accent (skip link) | 4.5:1 against the accent |
| `--rb-color-focus` | focus ring, aliases the accent | **3:1** on page, subtle **and code** backgrounds |

### Code block

| Token | Purpose | Gated at |
|---|---|---|
| `--rb-code-bg` · `--rb-code-text` · `--rb-code-border` | the block | 4.5:1 |
| `--rb-code-chrome-fg` / `-hover` | copy and wrap controls at rest / hover | 4.5:1 |
| `--rb-code-gutter-fg` | line numbers | 4.5:1 |
| `--rb-code-output-bg` | `{output=true}` muted treatment (Q3) | code text 4.5:1 on it |
| `--rb-code-hl-bg` | `{hl_lines=…}` band | every token 4.5:1 **on it** |
| `--rb-code-hl-border` | `{hl_lines=…}` inline-start marker | **3:1** |

> `--rb-code-hl-border` is **new in this workstream and not yet consumed.** `code.css` is owned by
> the code-block workstream; the marker wants
> `.highlight .line.hl { border-inline-start: 2px solid var(--rb-code-hl-border); }`.
> Until then the highlight is carried by the background tint alone.

#### Why the highlight band is shallow, and why that is correct

The tint is deliberately faint — 1.43:1 (light), 1.35:1 (dark) against `--rb-code-bg`. The binding
constraint runs the other way: **every syntax token has to keep 4.5:1 once that background slides
underneath it**, and a tint deep enough to clear 3:1 on its own would push half the palette below AA.

WCAG's ratio is also the wrong instrument for two *backgrounds*. It is a luminance ratio, and
near-black luminances are compressed enough that two visibly distinct dark bands score ~1.1:1. So
the 1.35 floor in the gate is labelled as a **perceptibility floor, explicitly not a WCAG claim**;
the conformant 1.4.11 signal is `--rb-code-hl-border` at 3:1.

### Table of contents

`--rb-toc-fg`, `--rb-toc-fg-active`, `--rb-toc-marker` — aliases of the muted/accent tokens,
declared separately so the templates workstream has a name to consume and so the selected-entry
contrast is asserted.

### Type, space, shape

`--rb-font-sans` / `--rb-font-mono` and their `-system` variants; `--rb-text-*` (base 17px),
`--rb-leading-*`, `--rb-weight-*`; `--rb-space-1..8` on a 4px base; `--rb-radius-*`;
`--rb-measure` 70ch, `--rb-content-width`, `--rb-page-width`, `--rb-gutter`; `--rb-target-min` 24px,
`--rb-focus-width`, `--rb-focus-offset`; `--rb-transition`; `--rb-z-*`.

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
