# Implementation contracts

**Status:** in force from the M1 foundation commit
**Audience:** anyone working on Runbook, human or agent

The [specs](../specs/) say what to build. This file says **who owns which file**, so four
workstreams can run in parallel worktrees without stepping on each other, and pins the interfaces
between them.

Two rules:

1. **Do not edit a file another workstream owns.** If you need something changed there, say so in
   your PR description and let the owner change it. A cross-boundary edit is a merge conflict.
2. **Names in the shared contracts below are frozen.** Adding is fine. Renaming is not, because the
   rename lands in someone else's file.

---

## 0. Round 2 — the current split

M0–M2 and most of M4a are merged. §1 below is the round-1 map and is kept because it still records
which workstream authored what; **the table here supersedes it for work in flight.**

| Stream | Owns | Milestone |
|---|---|---|
| **E — citizix migration parity** | `scripts/check_parity.py`, `docs/migration.md`, `.github/workflows/parity.yml` | M3 |
| **F — Client-side search** | `layouts/search.html`, `layouts/_partials/search/**`, `layouts/index.json`, `assets/js/search/**`, `assets/css/search.css`, `exampleSite/hugo.toml`, `docs/search.md` | M4b |
| **G — Shortcodes** | `layouts/shortcodes/**`, `assets/css/components.css`, `docs/shortcodes.md` | M4b |
| **H — Release hygiene** | `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/**`, `.github/PULL_REQUEST_TEMPLATE.md`, `docs/accessibility.md`, `docs/configuration.md` | M5 |

Shared files and how they are kept out of each other's way:

- **`assets/css/components.css` and `assets/css/search.css` are already wired into the concat list
  in `head/css.html`.** Neither G nor F edits that file. `with resources.Get` skips a stylesheet
  that does not exist, so an empty one is harmless.
- **`i18n/en.yaml`** — F appends only under `# ── Search ──`, G only under `# ── Shortcodes ──`.
  Both sections already exist. Staying inside your own section is what keeps the merge clean.
- **`exampleSite/content/**`** — each stream adds its own new files and edits nobody else's.
- **`assets/js/runbook.js` stays frozen at three modules.** Search is a separate lazy chunk with its
  own entry and its own budget. Tabs get no JavaScript at all — see §2.3.
- **`docs/configuration.md`** is H's. E, F and G record new settings in their own doc and list them
  in the PR body; H folds them into the reference.

---

## 1. File ownership — round 1 (historical)

### A — Design system

| Path | Notes |
|---|---|
| `assets/css/tokens.css` | Token **values**. The names are a shared contract — see §2 |
| `assets/css/base.css` | Element defaults, prose typography |
| `assets/css/layout.css` | Page shell, header, footer, list views |
| `assets/css/chroma-light.css` · `chroma-dark.css` | Syntax palettes, shell-tuned |
| `assets/css/print.css` | |
| `assets/js/modules/theme.js` | |
| `layouts/_partials/head/theme-guard.html` | |
| `static/fonts/**`, `assets/fonts/**` | |
| `scripts/check_contrast.py` | |
| `docs/design-tokens.md` | |

### B — Code block

| Path | Notes |
|---|---|
| `layouts/_markup/render-codeblock.html` | |
| `assets/css/code.css` | |
| `assets/js/modules/code.js` | |
| `docs/code-blocks.md` | |

### C — Templates, SEO, taxonomy

| Path | Notes |
|---|---|
| `layouts/*.html` | `baseof`, `home`, `page`, `list`, `section`, `taxonomy`, `term`, `404` |
| `layouts/_partials/**` | except `head/theme-guard.html` (A) |
| `layouts/_markup/render-{link,image,heading}.html` | not `render-codeblock` (B) |
| `layouts/shortcodes/**` | |
| `assets/js/modules/toc.js` | |
| `i18n/en.yaml` | append to your own section |
| `archetypes/**`, `exampleSite/hugo.toml` | |
| `docs/configuration.md`, `docs/extending.md` | |

### D — Fixtures, CI, verification

| Path | Notes |
|---|---|
| `exampleSite/content/**` | not `exampleSite/hugo.toml` (C) |
| `.github/**` | |
| `scripts/check_*.py` | except `check_contrast.py` (A) |
| `docs/verification.md` | |

### Nobody

`README.md`, `LICENSE`, `theme.toml`, `hugo.toml`, `specs/**`, this file. Raise a separate PR.

---

## 2. Shared contracts

### 2.1 CSS custom properties

Declared in `assets/css/tokens.css`, prefixed `--rb-`. B and C consume them by name; A owns the
values. The full list is in that file — read it before inventing a token.

Load order in `_partials/head/css.html` is the cascade contract, and a file missing from disk is
skipped rather than fatal, so each stylesheet can land independently:

```
tokens → base → layout → code → chroma-light → chroma-dark → print
```

### 2.2 Theme switching

Three states on `<html data-theme>`: `auto`, `light`, `dark`. CSS must already be correct for all
three **before** JavaScript runs; `head/theme-guard.html` only ever changes the answer.

```css
:root, :root[data-theme="light"]                        /* light */
:root[data-theme="dark"]                                /* dark  */
@media (prefers-color-scheme: dark) { :root[data-theme="auto"] { /* dark */ } }
```

Storage key `runbook:theme:v1`, every access in `try`/`catch`.

### 2.3 JavaScript

`assets/js/runbook.js` is **frozen**: it imports three modules, guards each in `try`/`catch`, and
boots on `DOMContentLoaded`. Own your module, not the entry.

Everything reachable from it shares **one 3 KB gzipped budget**. Search is not imported there — it
is a separate lazy chunk on `/search/` with its own 3 KB.

### 2.4 Configuration

Namespace is **`params.runbook.*`** — this resolves open decision Q6 in
[006](../specs/006-architecture-decisions.md), and supersedes the informal `params.taxonomyTitles`
spelling in [004](../specs/004-hugo-mechanics.md) §4a. The key is `params.runbook.taxonomyTitles`.

Nothing is read from a bare top-level param, so Runbook can never collide with a consumer's own
keys. Every new setting gets a default in the root `hugo.toml` and an entry in
`docs/configuration.md`.

### 2.5 Strings

Every user-visible string comes from `i18n/en.yaml`. No exceptions — a hard-coded string cannot be
translated, and retrofitting means touching every layout.

### 2.6 Markup hooks

`layouts/_partials/hooks/` holds the six ADR-8 extension points. They are **empty on purpose** and
stay that way in the theme; the theme ships no analytics, no ads, no comment vendor and no live IDs.

---

## 3. Verified Hugo behaviour

Measured on **v0.164.0+extended**, 2026-07-28, against `exampleSite`. These were tested rather than
assumed, and they change how the code is written.

**`.Options` is fence-only; it does not merge site config.** Built against a site forcing
`lineNos=true, lineNumbersInTable=true`, a block that did not opt in reported `map[hl_lines:3-4]`
with no `linenos` key; the block carrying `{linenos=true}` reported `map[linenos:true]`. So
`.Options` is safe to read for the per-block opt-in.

**The leak is inside `transform.Highlight`,** which applies the site's defaults for any key the
caller leaves unset. That is why the hook passes `lineNos` and `lineNumbersInTable` on *every* call
rather than only when true. **An unset key is where the consumer's config gets back in.**

**Proof it works:** the `exampleSite` build is byte-identical with and without
`HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true`. This belongs in
CI (specs/007 §2 Layer 2) — it is a cheaper and stricter check than the archive smoke build, and it
runs on every PR.

**Attribute routing** ([004](../specs/004-hugo-mechanics.md) §1) confirmed: Chroma-known keys
(`linenos`, `hl_lines`) land in `.Options` with lowercase names; unknown keys (`file`, `prompt`,
`output`) land in `.Attributes`.

**Chroma emits `<pre tabindex="0">` unconditionally,** which contradicts REQ-CB-6. There is no
`transform.Highlight` option to suppress it; the hook must strip it and let the JS re-add it only
to blocks that actually overflow.

**Highlighted lines are `<span class="line hl">`.** A bare `.hl` selector matches nothing.

### Deprecations vs the version floor

ADR-0 declares `min_version = 0.146.0`, and Hugo v0.158.0 deprecated three things the theme needs:
`languageCode`, `.Language.LanguageCode`, `.Language.LanguageDirection`. Their replacements
(`locale`, `.Locale`, `.Direction`) **do not exist at the 0.146.0 floor**, so using either side
breaks a supported version.

Runbook uses accessors that are stable across the whole range — `site.Language.Lang` and a language
param for direction — and omits `languageCode` from its own configs. This matters because CI builds
with `--panicOnWarning` (specs/007 §3.5), which a deprecation warning would trip.

RTL is configured per language:

```toml
[languages.ar.params]
  direction = "rtl"
```

---

## 4. Building it

```bash
# dev server
hugo server --source exampleSite --themesDir ../.. --disableFastRender

# what CI does
hugo --source exampleSite --themesDir ../.. --destination ../public \
     --cleanDestinationDir --panicOnWarning --printPathWarnings

# REQ-CB-1 proof — output must be identical to the run above
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true \
  hugo --source exampleSite --themesDir ../.. --destination ../public-hostile --cleanDestinationDir

# budgets — the -n is mandatory, without it gzip embeds a timestamp and CI goes flaky
gzip -n -9 -c public/<path>/index.html | wc -c
```
