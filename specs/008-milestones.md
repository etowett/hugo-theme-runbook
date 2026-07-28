# 008 — Milestones

**Status:** specification
**Last revised:** 2026-07-28
**Supersedes:** issue #1 §7

---

## What changed from the original plan

Issue #1's M1–M6 had the right instincts but three structural problems: the example site, CI and
migration parity were all deferred to the end; M4 bundled unrelated products (shortcodes, series,
search, SEO); and M2's justification rested on §3.4's WordPress-legacy figure, which is now zero.

**M2 survives, on stronger grounds.** The differentiator was never the deleted WordPress markup. It
is 9,046 code blocks at 18.2 per post — up 71% since the issue was written — 79% shell, 45.2%
single-line, and 1,586 blocks with horizontal overflow. The code block is the product.

---

## M0 — Contracts and fixtures

Nothing is built until the contracts are pinned. This milestone is mostly decisions and measurement.

- Close the six open decisions in [006](006-architecture-decisions.md) §"Decisions still open" that
  are needed by M1.
- Pin the theme configuration API: namespace, feature flags, defaults, precedence.
- Pin the measurable budgets and the fixture page list ([005](005-performance-budgets.md),
  [007](007-verification.md)).
- Emit the baseline URL manifest from the current Stack build
  ([010](010-citizix-migration.md) §2).
- **Fix the two citizix content bugs** ([010](010-citizix-migration.md) §1) — separate PRs in the
  citizix repo, merged before theme work starts.
- Commit the corpus profiler to `scripts/` so [002](002-corpus-profile.md) is reproducible and can
  act as a drift detector.

## M1 — Minimum vertical slice

A theme that builds, deploys and is publishable — thin but complete end to end. Documentation and CI
start **here**, not at the end.

- Repo scaffold on the **new Hugo template system** ([006](006-architecture-decisions.md) ADR-0):
  `layouts/_markup/`, `layouts/_partials/`, `page.html`, `home.html`.
- `theme.toml`, root `hugo.toml` with `[module.hugoVersion]`, MIT `LICENSE`.
- `exampleSite/` skeleton — it is the fixture host and the future showcase demo.
- CI building against **both minimum and latest Hugo**.
- CSS custom-property token system; both palettes; theme toggle with the no-flash guard.
- `baseof`, home, page, list, 404.
- System font stack (bundled font deferred to M2).
- **Extension hooks** ([006](006-architecture-decisions.md) ADR-8) — stubbed and documented now, so
  nothing later has to be retrofitted around them.
- `i18n/en.yaml` with every UI string from day one.
- `archetypes/default.md`.
- Configuration reference started.

## M2 — The code system

The differentiator. Get it right before anything else is built on top.

- `render-codeblock.html` implementing REQ-CB-1 … REQ-CB-8
  ([003](003-design-spec.md) §3.3).
- **REQ-CB-1 first** — never forward site line-number config. Verified by the archive smoke build
  asserting zero `lntable` output despite citizix's site config
  ([007](007-verification.md) §2 Layer 2).
- Uniform chrome, copy, wrap toggle, overflow detection, opt-in line numbers, line highlighting,
  filename, output treatment, prompt-aware copy.
- Dual Chroma palettes, **shell tokens tuned first**, every token contrast-verified in CI.
- Bare `pre > code` parity — one paragraph of CSS, no `wp-block-*` styling.
- Self-hosted subset font with box-drawing coverage (REQ-FONT-1), plus the zero-byte system fallback.
- **Write the synthetic code fixtures here**, alongside the features, not at the end
  ([007](007-verification.md) §2 Layer 1).
- Contrast, overflow, touch, keyboard and zero-JS tests for the code block.

## M3 — citizix migration parity

Deliberately early. Migration is where a theme discovers what it actually has to support, and
discovering that at M6 is too late to act on.

- Port or replace all ten local override files ([010](010-citizix-migration.md) §3).
- Correct JSON-LD without `articleBody`; fix the double-encoded values.
- Full URL / alias / canonical / RSS / sitemap / OG parity manifest diff.
- Reversible preview deployment with a confirmed rollback command.

## M4a — Navigation and discovery

- Static anchor TOC. **Scroll-spy only if its JS cost fits the core budget** alongside copy, wrap and
  overflow detection.
- Related posts as a footer component, with relevance tested against citizix's actual weighting.
- Pagination, taxonomy and term pages, archive.
- Taxonomy browse strategy for 159 single-use tags.
- Empty, single-item and high-cardinality states for every list view.

## M4b — Optional content features

- Shortcodes: admonition first; tabs, details and filetree only as justified.
- Series — requires the consumer to register the taxonomy in site config, so it ships **with
  documentation or not at all**.
- Client-side search over a **metadata-only** index ([005](005-performance-budgets.md) §4), on its
  own budget and its own lazy chunk.

## M5 — Release hardening

- Full accessibility audit and the manual test matrix ([007](007-verification.md) §3.6).
- Contrast CI, budget distribution gates, zero-JS pass, strict-CSP build.
- Visual regression goldens committed with the documented update workflow.
- Cross-browser: automated Chrome and Firefox, manual Safari and iOS Safari.
- Print stylesheet.
- Security review: search-result escaping, code metadata handling, URL handling, SVG handling.
- Accessibility support statement.
- `CHANGELOG.md`, `CONTRIBUTING.md`, security policy, issue templates, Dependabot.
- Complete configuration reference, migration guide, override examples, upgrade/deprecation policy.
- Tagged semver release.

## M6 — Ship

1. citizix staged preview, URL and link comparison, production cutover with rollback ready.
2. Observe production for a defined period.
3. Screenshots at showcase dimensions (minimum 1500×1000 and 900×600, 3:2, PNG or JPG).
4. Deploy the `exampleSite` demo — **this is the showcase demo, not citizix**
   ([009](009-showcase-compliance.md) §3).
5. Submit: fork `gohugoio/hugoThemesSiteBuilder`, add the theme URL to `themes.txt` in
   lexicographical order, open a **pull request**, confirm the Netlify preview succeeds.
6. Stand up the scheduled latest-Hugo CI job before the showcase's daily rebuild finds a regression
   first.

> **euxven.com is not in this sequence.** It was removed from scope entirely — see
> [001](001-overview.md) §2. The rollout is citizix.com → showcase submission.
