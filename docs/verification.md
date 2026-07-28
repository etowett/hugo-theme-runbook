# Verification

**Status:** stub — owned by the fixtures/CI workstream. Plan is [007](../specs/007-verification.md).

## Reproducibility

`gzip -n -9` throughout. **The `-n` is mandatory** — without it gzip embeds a modification timestamp
in the header, byte counts vary between runs, and every budget gate goes flaky. A budget check that
omits it is not reproducible.

## The REQ-CB-1 assertion, cheaply

Build `exampleSite` twice and diff. The second build forces the reference site's own hostile
configuration through environment variables:

```bash
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true hugo …
```

The two outputs must be **identical**. This is stricter than "zero `lntable` in the archive build"
and it runs on every PR without needing the citizix content pinned. Verified working at the
foundation commit — see [contracts §3](contracts.md#3-verified-hugo-behaviour).

## To build

- Named tooling, per [007](../specs/007-verification.md) §3.4 — **Playwright** screenshots at 3
  viewports (360 / 768 / 1280), both themes, compared with **pixelmatch**. Interaction states, not
  just page loads: focused copy button, copied confirmation, wrap on and off, mobile nav open,
  active TOC item, tabs with and without JS
- The contrast gate — every prose pair and **every Chroma token** in both themes, plus focus rings,
  controls, links, selected TOC entries and highlighted-line backgrounds. Roughly 50 lines, and
  genuinely the differentiating quality check
- Budget gates: theme-shell budgets are hard ceilings; page-weight budgets are p50/p90 distribution
  gates with a no-regression rule, never a universal ceiling
- **JSON-LD parsed and asserted, never eyeballed.** Every block must `json.loads()`; for `Article`
  pages assert `headline` does not begin with a quote and `datePublished` matches
  `^\d{4}-\d{2}-\d{2}T`. Both assertions exist because the reference site shipped double-encoded
  JSON-LD on 493 of 493 article pages for months — **it parses**, so nothing short of a value-level
  assertion catches it
- Builds against **both** the declared minimum Hugo and latest, with `--panicOnWarning`
- A **scheduled** latest-Hugo job, independent of pushes — the showcase rebuilds every theme daily
  at 00:00 UTC and a theme that stops building disappears from it with no notice
- External link sweep **weekly, never per-PR** — it takes minutes, hits rate limits and fails when
  someone else's docs site is down. A red X nobody can act on teaches people to ignore CI. Open a
  tracking issue on failure, and give every exclusion-list entry **a reason**, or someone will
  "clean up" a real one
- Zero-JS pass, storage-disabled pass, strict-CSP build
- Lighthouse against the **exampleSite demo**, never production citizix: median of 5 runs, pinned
  browser and Lighthouse versions. A perfect automated score is reported as an automated score and
  never described as accessibility conformance
