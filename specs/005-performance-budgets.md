# 005 — Performance budgets

**Status:** measured, revised
**Date measured:** 2026-07-28
**Supersedes:** the §2 budget table in issue #1

---

## 1. The problem with the original budgets

Issue #1 §2 proposed four budgets, of which one is unachievable as stated and three are
under-specified.

The fatal one is **"Article HTML ≤ 7 KB gzip"** applied as a CI gate. Measured across all 493 pages
in the current build whose JSON-LD declares `@type: Article`, compressed with `gzip -n -9`:

| Statistic | Bytes (gzip) |
|---|---:|
| Minimum | 3,925 |
| **Median** | **10,663** |
| p75 | 12,637 |
| p90 | 15,488 |
| p95 | 18,915 |
| Maximum | 77,935 |

**Only 22 of 493 articles (4.5%) are at or below 7,000 gzipped bytes today.** A CI rule that failed
every article over 7 KB would fail 95.5% of the archive before Runbook added a single byte of its
own chrome.

The error is category, not calibration. Total page weight is dominated by **content** — a post with
5,756 prose words and a 767-line code block cannot be compressed into a fixed ceiling by any theme.
A theme can only be held responsible for the bytes it contributes.

## 2. Current baseline

`hugo --gc --minify`, Hugo v0.164.0+extended, hugo-theme-stack v4.0.3, 1,202 pages + 355 aliases,
build 3,987 ms. Compression is `gzip -n -9` throughout (the `-n` matters — without it gzip embeds a
timestamp and results are not reproducible).

| Asset | Raw | Gzip |
|---|---:|---:|
| CSS (1 file) | 55,687 | **10,110** |
| JS (3 files: main, gallery, search) | 13,990 | **4,778** |
| Sampled article — `how-to-merge-multiple-kubeconfig-files-into-one` | 34,109 | **8,091** |
| Homepage | 33,454 | **6,817** |

Also: **11 `<script>` tags** per article; **484 of 492** published pages emit
`<table class="lntable">`; **8,900** Chroma blocks build-wide.

### What the theme actually controls on an article page

| Transformation | Raw | Gzip | Saving (gz) |
|---|---:|---:|---:|
| As built today | 34,109 | 8,091 | — |
| Remove line-number tables | 31,984 | 7,982 | 109 B |
| Remove JSON-LD `articleBody` | 30,363 | 7,659 | 432 B |
| Remove all JSON-LD | 29,111 | 7,327 | 764 B |
| Remove line-number tables **and** `articleBody` | 28,238 | 7,541 | 550 B |

Two conclusions:

1. **Line numbers are not the biggest lever.** citizix's `layouts/partials/head/schema.html:52`
   emits the whole article plaintext a second time as JSON-LD `articleBody`. That single field costs
   4× what every line-number table on the page costs combined.
2. **The claim "Chroma markup is most of the page" is false.** It is a meaningful contributor, and
   removing inherited line numbers is still correct (see
   [004 — Hugo mechanics](004-hugo-mechanics.md) REQ-CB-1), but it does not dominate.

## 3. Revised budgets

Budgets are split by what is being measured, because "theme bytes" and "page bytes" have different
owners.

### 3.1 Theme-shell budgets — hard CI gates

Measured against a **synthetic fixture** with fixed, minimal content, so the number reflects only
what the theme emits.

| Asset | Budget (gzip) | Baseline | Notes |
|---|---:|---:|---|
| CSS, total | **≤ 8,000 B** | 10,110 B | Includes both palettes, all shortcode styles, print styles |
| Core article JS | **≤ 3,000 B** | ~2,873 B (main only) | Theme toggle, copy, wrap, TOC enhancement |
| Search JS (separate chunk, lazy) | **≤ 3,000 B** | 1,734 B | Loaded only on `/search/` |
| Search index JSON | **≤ 250 KB** raw / **≤ 60 KB** gz | not built | See §4 |
| Bundled code font (if enabled) | **≤ 30 KB** per subset | 0 (uses Google Fonts) | Zero if system stack is used |
| `<script>` tags per article | **≤ 2** | 11 | Inline theme guard + one deferred bundle |
| Third-party hosts added by the theme | **0** | 2 (`fonts.googleapis.com`, `fonts.gstatic.com`) | Site-owner integrations excluded |

> ### ⚠️ Re-baseline required before M3
>
> **Measured 2026-07-28 (evening).** Since §2 was written, the reference site fixed its JSON-LD
> (removing a duplicated full-text `articleBody`) and turned off site-wide line numbers — citizix#62.
> Those changes alone moved the article distribution:
>
> | | When §3.2 was set | Now, still on Stack |
> |---|--:|--:|
> | Median article | 10,663 B gz | **9,159 B** |
> | p90 | 15,488 B gz | **11,626 B** |
> | Max | 77,935 B gz | **47,509 B** |
> | Archive total | 5.59 MiB | **4.56 MiB** |
> | Articles under 7 KB gz | 22 (4.5%) | **45 (9.1%)** |
>
> The p50 gate below was set to ≤9,000 B against a 10,663 B median. The median is now 9,159 B
> **without Runbook existing yet**, so that gate now measures almost nothing. The p90 gate of
> ≤14,000 B is already met by 11,626 B.
>
> **Re-derive §3.2 from a fresh Stack baseline at the start of M3.** More generally: a
> "no-regression against Stack" gate is only meaningful against a baseline captured at the same
> commit as the comparison, so the baseline must be regenerated, not copied from this document.
>
> The theme-shell budgets in §3.1 are unaffected — CSS is still 10,031 B gz, JS 4,778 B gz, and an
> article still carries 11 `<script>` tags.

### 3.2 Page-weight budgets — distribution gates, not ceilings

Measured across the **real citizix archive**, gating the *distribution* rather than every page.

| Page class | Gate |
|---|---|
| Article, median (p50) | **≤ 9,000 B gz** — a 15.6% improvement on today's 10,663 |
| Article, p90 | **≤ 14,000 B gz** — a 9.6% improvement on today's 15,488 |
| Article, worst case | **must not regress** against the Stack baseline for the same page |
| Homepage | **≤ 6,000 B gz** — from 6,817 |
| Taxonomy / list page | **≤ 6,000 B gz** |

Rationale: the theme cannot shrink content, but it must never make a given page *heavier* than Stack
rendered it. Regression against a per-page baseline is the meaningful test; an absolute ceiling is
not.

### 3.3 Named fixtures

Every budget above is measured against a pinned set of pages so results are comparable across runs.
Fixture selection is specified in [007 — Verification](007-verification.md); at minimum it must
include the median article, the p90 code-heavy article, the 158-block article, the 767-line-block
article, the 854-char-line article, a table article, a no-code article, and the longest-prose
article.

## 4. Budgets the original spec omitted entirely

**Fonts.** Issue #1 mandates self-hosted JetBrains Mono but sets no byte budget for it, and font
bytes do not appear in the CSS figure. A subset WOFF2 is typically 25–40 KB — comparable to the
entire CSS budget. Decisions required: is the font bundled by default or opt-in; what is the subset;
what is the `font-display` behaviour; and is there a zero-byte system-monospace fallback. See
[003 — Design specification](003-design-spec.md) §3.1.

**Search index.** "Build-time JSON index" is an architecture, not a budget. At 497 posts the index
size depends entirely on whether code blocks are indexed. Required decisions: indexed fields;
whether code content is included; draft/future exclusion; maximum response size; and cache policy.

**Print.** Technical procedures get printed and saved as PDF. No budget or behaviour is currently
specified for print styles — code overflow, hidden controls, and page breaks all need deliberate
handling.

## 5. Reproducibility

Every measurement in this document is reproducible with:

```bash
hugo --gc --minify --destination public
gzip -n -9 -c public/<path>/index.html | wc -c
```

`gzip -n` is required. Without `-n`, gzip embeds a modification timestamp in the header and byte
counts vary between runs, making CI gates flaky. Any budget check that omits it is not reproducible.
