# Changelog

All notable changes to the Runbook Hugo theme are recorded here.

The format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/), and the project
follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) as scoped in
[Versioning, upgrades and deprecation](#versioning-upgrades-and-deprecation) below.

---

## Versioning, upgrades and deprecation

**There is no released version yet.** Until `v1.0.0`, `main` moves and the guarantees below describe
what will hold from the first tag, not what holds today. Pin a commit if you depend on this now.

### What semver covers

A theme has no function signatures, so "public API" has to be named explicitly. For Runbook it is
these six surfaces, and nothing else:

| Surface | Where |
|---|---|
| 1. Configuration keys | `params.runbook.*` — [configuration reference](docs/configuration.md) |
| 2. Front-matter keys | the schema in [`archetypes/default.md`](archetypes/default.md) |
| 3. The six override hooks | `layouts/_partials/hooks/*.html` — [ADR-8](specs/006-architecture-decisions.md), [extending](docs/extending.md) |
| 4. CSS custom properties | the `--rb-*` tokens in `assets/css/tokens.css` — [design tokens](docs/design-tokens.md) |
| 5. Code-block fence attributes | `file`, `caption`, `prompt`, `output`, `linenos`, `hl_lines` — [code blocks](docs/code-blocks.md) |
| 6. The declared Hugo version floor | `min_version` in `theme.toml` |

- **MAJOR** — removing or renaming anything in the six surfaces; raising `min_version`; changing a
  default that visibly changes a page without any configuration change on the consumer's side.
- **MINOR** — new keys, new hooks, new tokens, new shortcodes, new fence attributes; a visual change
  that is opt-in.
- **PATCH** — bug fixes, contrast and accessibility corrections, documentation, CI.

**Class names other than the `--rb-*` tokens are not API.** If you style `.rb-code-btn` from your own
CSS, that can break in a minor release. The hooks and the tokens exist so you do not have to.

### Deprecation window

A surface is never removed in the release that deprecates it.

1. **Deprecate** in a minor release: the old spelling keeps working, the CHANGELOG says what replaces
   it, and the documentation marks it deprecated at the point of use.
2. **Warn** with `warnf` where a template can detect the old usage, so a build with
   `--panicOnWarning` surfaces it loudly and every other build surfaces it quietly.
3. **Remove** no earlier than the next major release, and never less than **90 days** after the
   deprecating release.

### Latest-Hugo breakage

The Hugo Themes showcase rebuilds every theme **daily at 00:00 UTC** against the latest Hugo release,
and a theme that stops building disappears from the showcase with no notice and no message
([specs/009 §4](specs/009-showcase-compliance.md)). That is the reason this policy is written down:

- CI builds the demo against latest Hugo on a schedule at **22:00 UTC daily** — two hours before the
  showcase rebuild, deliberately, so this project finds the break first — and opens a tracking issue
  on failure rather than only turning a square red.
- **A build failure against the latest Hugo release is treated as a P1**: it is triaged within
  **72 hours** and a patch release is cut as soon as a fix exists.
- Every pull request builds against **both** the declared floor (non-extended) and latest. Both legs
  can break independently, so both are blocking.
- **Raising `min_version` is a major release**, without exception. The floor is a promise in
  `theme.toml` and in `[module.hugoVersion]`, and quietly using a function that does not exist at the
  floor breaks it just as thoroughly as editing the number.

### Support

The **latest release** is supported. Older majors receive security fixes only, for **six months**
after the next major is tagged. Security reporting is in [SECURITY.md](SECURITY.md); accessibility
barriers are handled on the same footing as build breaks
([accessibility statement §4](docs/accessibility.md)).

---

## [Unreleased]

Everything below is pre-release work on `main`. It is grouped by what it does rather than by the
milestone that produced it; milestone definitions are in [specs/008](specs/008-milestones.md).

### Added

**Theme foundation (M1)**

- Repository scaffold on Hugo's post-v0.146.0 template system — `layouts/_markup/`,
  `layouts/_partials/`, `page.html`, `home.html`. No legacy `_default/` tree
  ([ADR-0](specs/006-architecture-decisions.md)).
- `theme.toml`, a root `hugo.toml` with `[module.hugoVersion]`, and an MIT `LICENSE` — the showcase
  requirements from [specs/009 §2](specs/009-showcase-compliance.md).
- `exampleSite/`, which is both the future showcase demo and the synthetic fixture host.
- The `params.runbook.*` configuration namespace, resolved in one place
  (`_partials/utils/settings.html`) with `isset` probes so a setting of `false` is honoured.
- Six empty, documented override hooks — `custom-head`, `custom-body-start`, `custom-body-end`,
  `comments`, `article-footer`, `custom-schema` ([ADR-8](specs/006-architecture-decisions.md)).
- `i18n/en.yaml` carrying every user-visible string from the first commit.
- `archetypes/default.md`, annotated, matching the documented front-matter schema.

**Design system (M1)**

- A `--rb-*` CSS custom-property token system, assembled by Hugo's own pipeline into a single
  stylesheet — minified, fingerprinted and SRI-tagged in production builds. No Node, no Sass, no
  external toolchain ([ADR-1](specs/006-architecture-decisions.md)).
- Light and dark palettes, plus light and dark Chroma palettes, scoped under `:root[data-theme]`
  ([ADR-2](specs/006-architecture-decisions.md)). Accent hue azure ≈ 212°, chosen because it clears
  4.5:1 as text on both backgrounds without changing hue between themes.
- The no-flash theme guard: a ~160-byte inline blocking script, storage key `runbook:theme:v1`,
  every `localStorage` access in `try`/`catch`, and CSS already correct for all three states before
  it runs ([ADR-4](specs/006-architecture-decisions.md)).
- A 25,032-byte JetBrains Mono subset with full Box Drawing and Block Elements coverage, plus the
  zero-byte system fallback behind `bundledCodeFont = false`
  ([ADR-6](specs/006-architecture-decisions.md), REQ-FONT-1).
- Print stylesheet.

**The code block (M2)**

- `layouts/_markup/render-codeblock.html` implementing REQ-CB-1 … REQ-CB-8.
- **REQ-CB-1:** the hook builds its Chroma option set from scratch and passes every
  structure-changing key on every call, so a consuming site's `markup.highlight` settings cannot
  restructure Runbook's markup. CI asserts the build is byte-identical with `lineNos` and
  `lineNumbersInTable` forced on.
- Chrome that appears only when it has something to say: no header bar unless `file=` or `caption=`
  is present; a muted corner language tag and controls otherwise.
- Copy and wrap controls that ship `hidden` and are unhidden only when they can work. Copy falls back
  to a detached `<textarea>` and `execCommand`, and hides itself if both paths fail.
- `{prompt="$"}` opt-in copy semantics — commands only, prompt stripped, `\`-continuations kept
  whole. Never inferred from block content ([Q2](specs/006-architecture-decisions.md)).
- `{output=true}` / an `output` fence: muted, forced through the plaintext lexer, no copy button
  ([Q3](specs/006-architecture-decisions.md)).
- Horizontal scroll with `tabindex` applied **by measurement** — on load, on resize, and after
  `document.fonts.ready` — rather than Chroma's unconditional `<pre tabindex="0">`.
- Display labels only for the shell family (`sh` → `Shell`); no language normalisation
  ([Q1](specs/006-architecture-decisions.md)).
- Bare `pre > code` parity, so 4-space indented blocks — which bypass the render hook in every Hugo
  version — match the enhanced case property for property ([ADR-3](specs/006-architecture-decisions.md)).

**Templates, SEO and taxonomy (M4a)**

- `baseof`, `home`, `page`, `list`, `section`, `taxonomy`, `term`, `archive`, `404`, `rss.xml`.
- Static anchor table of contents built from `.Fragments`, with optional scroll-spy. The anchors are
  the feature; scroll-spy is an enhancement.
- Related posts with an empty-result fallback to recent posts in the same section.
- Pagination, term and taxonomy browse pages, a collapsible "Rarely used" group behind
  `taxonomy.rareThreshold`, and real empty/single-item states for every list view.
- **REQ-TAX-1** rendered term titles: front matter, then `params.runbook.taxonomyTitles`, then
  title-casing. Replaces the 60 `_index.md` files the reference site carries purely to fix
  capitalisation; a site with zero such files renders correctly.
- JSON-LD that is correct by construction — asserted in CI to parse, to carry a `headline` that does
  not begin with a quote, and a `datePublished` matching `^\d{4}-\d{2}-\d{2}T`. The reference site
  shipped double-encoded JSON-LD on 493 of 493 article pages for months, which parses; nothing short
  of a value-level assertion catches it.
- Open Graph, Twitter cards, canonical URLs, sitemap and RSS. **No `<meta name="keywords">`**, and no
  `articleBody` in JSON-LD — both are specified prohibitions.
- Series navigation, previous/next, reading time, and a byline that shows "Updated" only when
  `lastmod` is genuinely later than `date`.
- `admonition` and `details` shortcodes; `details` is native `<details>` with zero JavaScript.
- Link and image render hooks: external links get `rel="noopener noreferrer"` and a CSS indicator,
  `target="_blank"` is off by default, and images carry real `width`/`height` whenever the
  destination resolves to a page resource.

**Verification and CI**

- Layer-1 synthetic fixtures in `exampleSite/content/`, including a one-URL code-block torture page,
  a 158-block page, a 767-line block, an 854-character line, box-drawing output, RTL text and a
  no-code post. The two large fixtures are generated deterministically and CI fails if regeneration
  would change anything.
- `scripts/check_contrast.py` — **150 WCAG 2.2 AA assertions across both themes**, every Chroma
  token against every background that can slide underneath it, non-text pairs at 3:1, plus
  deuteranopia and protanopia simulation and a 25° accent-hue guard.
- `scripts/check_reqcb1.py` — builds twice and asserts byte identity under hostile highlight config.
- `scripts/check_fixtures.py`, `check_jsonld.py`, `check_budgets.py`, `check_links.py`,
  `check_showcase.py`.
- CI on every push and pull request, building against **Hugo 0.146.0 non-extended and latest
  extended**, with `--panicOnWarning --printPathWarnings --printUnusedTemplates`, plus a
  hostile-consumer-configuration build permutation step.
- Scheduled jobs: a daily latest-Hugo build at 22:00 UTC and a weekly external link sweep, both
  opening a tracking issue on failure.
- Dependabot for GitHub Actions.
- Playwright and Lighthouse configurations, pinned but **not yet wired to a workflow**.

**Documentation**

- [`docs/configuration.md`](docs/configuration.md) — every `params.runbook.*` key with type, default
  and effect; the front-matter schema; per-page override precedence; and a Content Security Policy
  section carrying the theme-guard hashes and how to regenerate them.
- [`docs/accessibility.md`](docs/accessibility.md) — conformance target, what was tested and how, and
  an explicit list of what has **not** been tested.
- [`docs/code-blocks.md`](docs/code-blocks.md), [`docs/design-tokens.md`](docs/design-tokens.md),
  [`docs/extending.md`](docs/extending.md), [`docs/verification.md`](docs/verification.md),
  [`docs/contracts.md`](docs/contracts.md).
- `specs/001`–`specs/010`, recording every decision with the measurement behind it.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, issue templates and a pull-request template.

### Known issues

- **`params.runbook.accent` is declared and unread.** No template or stylesheet consumes it. Override
  `--rb-color-accent` from the `custom-head.html` hook instead — see
  [configuration](docs/configuration.md#appearance).
- **`params.runbook.themeColor.*` is shadowed.** `head/theme-guard.html` and `head/seo.html` both
  emit `<meta name="theme-color">`, so a build carries four of them and the hard-coded pair from the
  guard wins. Setting the keys currently has no visible effect.
- **The table of contents has no styling yet** — it renders as an ordinary ordered list.
- **No screenshots.** `images/screenshot.*` and `images/tn.*` do not exist, so
  `scripts/check_showcase.py` still reports two TODOs. They are deliberately not faked: a placeholder
  would make the check pass while the real showcase submission failed. See
  [CONTRIBUTING](CONTRIBUTING.md).
- **The demo site is not deployed.** `theme.toml` declares
  `https://hugo-theme-runbook.netlify.app/`, which currently returns 404. Standing it up is an M6
  task.
- The accessibility statement's [§3](docs/accessibility.md) is a list of untested areas, not a list
  of passing ones. Read it before assuming coverage.

### Not yet built

Client-side search, further shortcodes, the citizix migration guide and parity manifest, visual
regression baselines, the Lighthouse workflow, the archive smoke build, and a tagged release.

[Unreleased]: https://github.com/etowett/hugo-theme-runbook/commits/main
