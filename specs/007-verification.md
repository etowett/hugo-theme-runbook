# 007 — Verification plan

**Status:** specification
**Last revised:** 2026-07-28
**Supersedes:** issue #1 §6

---

## 1. What was wrong with the original plan

Issue #1 §6 proposed validating the theme "against the real 497-post archive" with a fixed set of
seven fixture pages, a Lighthouse 100/100/100/100 gate, and a Stack-vs-Runbook screenshot comparison.

Three problems:

**The fixture list is now impossible.** Of the seven required pages, three no longer exist: "a
raw-`wp-block-code` post" (zero remain), "an indented-code post" (one remains, and it is a content bug
to be fixed), and "a 12,788-word post" (the longest is now 5,756 words).

**Stack-vs-Runbook screenshot diffing is not a regression test.** It is a redesign comparison. The
two themes are meant to look different; expected differences would swamp any real regression.

**Lighthouse 100×4 as a hard gate is a trap.** The performance score is variance-prone on CI runners,
a perfect automated accessibility score is not WCAG conformance, and the gate never says *where* it
runs. It cannot run against production citizix — AdSense and GTM put 100 permanently out of reach,
and the showcase's own rules forbid live tracking credentials in `exampleSite`.

## 2. Two-layer fixture strategy

### Layer 1 — synthetic fixtures inside the theme repo

Committed to `exampleSite/content/`. These survive content cleanups in the reference archive — which
the original fixture list demonstrably did not — and they are what protects third-party robustness
after citizix stops exercising these cases.

Required code fixtures, all on one torture page plus targeted pages:

| Fixture | Guards |
|---|---|
| One-line block | REQ-CB-2 uniform chrome |
| Two- and three-line blocks | REQ-CB-2 |
| Fence with no language | Hook fires, `.Type` empty ([004](004-hugo-mechanics.md) §1) |
| Tilde fence | Hook fires |
| Unsupported / unknown language | Lexer fallback |
| 4-space indented block | REQ-CB-8, bare `pre > code` |
| Bare `<pre>` via unsafe HTML | REQ-CB-8, third-party robustness |
| 854-char single line | REQ-CB-5 horizontal scroll |
| 158-block page | Per-block JS cost, page weight |
| 767-line block | Long-block rendering |
| `{file=...}` and `{hl_lines=...}` | REQ-CB-7 attribute routing |
| `{linenos=true}` | REQ-CB-1 opt-in only |
| **`systemctl status` output with `└ ├ ─ ●`** | **REQ-FONT-1 subset coverage** |
| `{prompt="$"}` console block | Q2 copy semantics |
| `{output=true}` block | Q3 output treatment |
| Clipboard-unavailable context | REQ-CB-4 fallback |
| RTL context | i18n / `dir` |
| Table, admonition, tabs, no-code prose post | Layout and shortcodes |

### Layer 2 — archive smoke build

Build the real citizix content with Runbook in CI, with content as a pinned fixture (submodule or
tarball). Assertions:

- Page count matches the Stack build (1,202 pages + 355 aliases).
- Zero template errors; `hugo --printPathWarnings --printUnusedTemplates` clean.
- **Zero pages emitting bare `<pre><code>`** once the one content bug is fixed.
- **Zero pages emitting `<table class="lntable">`** — proves REQ-CB-1 works despite citizix's site
  config setting `lineNos: true`.
- Screenshot a small fixed page set (below).

Pin these real pages by path, selected from the current corpus:

| Role | Page |
|---|---|
| Median article | median of the gz distribution |
| p90 code-heavy article | p90 of the gz distribution |
| Most blocks (158) | the maximum-block post |
| Longest line (854 ch) | `2021-12-17-how-to-update-upgrade-debian-ubuntu-linux-using-ansible` |
| Longest prose (5,756 words) | the maximum-word post |
| Table post | any of the 32 |
| No-code post | any of the 6 |

**Do not preserve a malformed fence as a theme fixture.** Fix it in citizix
([010](010-citizix-migration.md) §1). Malformed source is tested synthetically only if the renderer
has a defined fallback.

## 3. Gates

### 3.1 Contrast — the check most themes lack

Automated WCAG 2.2 AA assertion over **every prose pair and every Chroma token pair, in both
themes**. The palettes are two generated CSS files: parse the declarations, compute the ratio of each
token colour against both block backgrounds, fail on any pair below threshold.

This is roughly a 50-line script and is genuinely the differentiating quality check. It must also
cover focus rings, controls, links, selected TOC entries and highlighted-line backgrounds — not only
token hex pairs.

### 3.2 Budgets

Per [005](005-performance-budgets.md). Theme-shell budgets are hard gates; page-weight budgets are
distribution gates (p50 / p90 / no-regression), never a universal ceiling.

All measurements use `gzip -n -9`. The `-n` is mandatory — without it gzip embeds a timestamp and CI
results are not reproducible.

### 3.3 Lighthouse — rewritten

Run Lighthouse CI against the built **exampleSite demo** (never against production citizix), with
pinned browser and Lighthouse versions, **median of 5 runs**:

| Category | Gate |
|---|---|
| Accessibility | 100 |
| Best practices | 100 |
| SEO | 100 |
| Performance | ≥ 98 |

Plus specific audits as hard assertions: no render-blocking resources, CLS = 0, tap targets pass.

Measure citizix production-like pages **separately**, reporting third-party effects independently
from first-party theme effects. A perfect automated score is reported as an automated score, never
described as accessibility conformance.

### 3.4 Visual regression

Named tooling, or it will not get built: **Playwright** screenshots, **3 viewports**
(360 / 768 / 1280), **both themes**, compared with **pixelmatch** against committed baselines with an
explicit diff threshold.

Specify and pin: browser version, device scale factor, OS font set, colour scheme, reduced-motion
state, and masks for dynamic regions. Define the approved-golden update workflow.

Interaction states must be captured, not just page loads: focused copy button, copied confirmation,
wrap toggle on and off, mobile navigation open, active TOC item, tabs with and without JS, and search
results.

### 3.5 Correctness and compatibility

- HTML validity; RSS/XML validity; JSON-LD validity; canonical URLs; OG values; sitemap output.
- **URL/alias manifest diff** between the Stack and Runbook builds — see
  [010](010-citizix-migration.md) §2.
- Internal link crawl against the production-equivalent build.
- Build with `unsafe: false`, `noClasses: false`, JS disabled, storage disabled, and a strict CSP.
- **Build against both the declared minimum Hugo version and latest Hugo.** The showcase uses latest.
- Zero-JS pass: every page navigable and readable with scripting disabled.

### 3.6 Manual

Automation cannot cover these; they are release checklist items:

Keyboard-only navigation · VoiceOver on an article page · touch interaction on iOS Safari ·
200% zoom and reflow · Windows High Contrast · `prefers-reduced-motion` · theme switching with
`localStorage` disabled · print / save-as-PDF.

Cross-browser: automate Chrome and Firefox with pinned versions; Safari and iOS Safari are manual.
"Chrome, Safari, Firefox, iOS Safari" as written in issue #1 is not a test matrix.

## 4. Accessibility support statement

Ship an accessibility statement documenting conformance target (WCAG 2.2 AA), what was tested, how,
and known limitations. Automated scores are not conformance certification and must not be presented
as such.
