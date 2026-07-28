# Configuration reference

**Status:** complete for every key that exists on `main` as of 2026-07-28. Coverage, and the keys
that are still arriving from other workstreams, are stated explicitly in
[§ Coverage and gaps](#coverage-and-gaps) — read it before assuming a key is missing by accident.

Every Runbook setting lives under **`params.runbook`**. Nothing is read from a bare top-level param,
so the theme cannot collide with a consumer's own keys or with another theme's. See
[contracts §2.4](contracts.md#24-configuration).

Defaults come from two places, and both are authoritative:

- the `[params.runbook]` block in the repo-root [`hugo.toml`](../hugo.toml), which Hugo merges
  *underneath* a consuming site's own configuration;
- `layouts/_partials/utils/settings.html`, which resolves every key with an inline default so the
  theme still behaves correctly when a consumer's config omits the block entirely.

> **Booleans that default to `true` are resolved with `isset`, not `| default true`.** `false |
> default true` is `true`, so the obvious spelling silently ignores anyone who turns a feature off.
> If you add a setting, follow the pattern already in `settings.html`.

## How a value is resolved

Highest wins:

1. **Page front matter** — but only for the keys listed under [Front matter](#front-matter). A
   setting with no front-matter row cannot be overridden per page.
2. **Your site's `params.runbook.*`** — `hugo.toml`, `config/_default/params.toml`, an environment
   override under `config/production/`, or a `HUGO_PARAMS_RUNBOOK_*` environment variable. Hugo's own
   configuration merge decides among these; Runbook sees only the result.
3. **The theme's `[params.runbook]`** in the repo-root `hugo.toml`, merged underneath yours by Hugo.
4. **The inline default in `utils/settings.html`**, which is what answers when the whole block is
   absent — for example when Runbook is loaded in a way that does not merge theme configuration.

Two consequences worth internalising:

- **A key you set to `false` is honoured.** Every boolean whose default is `true` is probed with
  `isset` rather than `| default true`, so "absent" and "present and false" are different answers.
- **Site configuration is not trusted where it changes structure.** `markup.highlight.lineNos`,
  `lineNumbersInTable`, `guessSyntax`, `noClasses`, `hl_inline`, `anchorLineNos` and `wrapperClass`
  are all forced by the code-block render hook on every call, so your values for them do not reach
  Runbook's blocks (REQ-CB-1). `markup.tableOfContents.startLevel`/`endLevel` are likewise ignored in
  favour of `params.runbook.toc.*`. Colour-only settings such as `markup.highlight.style` and
  `tabWidth` are left alone.

---

## Required of the consuming site

```toml
[markup.highlight]
  noClasses = false   # ADR-2 — inline Chroma styles make dual-theme highlighting impossible
```

Line-number settings need no attention: the render hook forces its own
([REQ-CB-1](../specs/004-hugo-mechanics.md#2-transformhighlight-inside-the-hook-inherits-the-consumers-site-config)),
so `lineNos = true` in a site config does nothing to Runbook.

To use the `series` taxonomy, register it — **a theme cannot register a taxonomy**, because
`[taxonomies]` is replaced wholesale rather than merged:

```toml
[taxonomies]
  tag = "tags"
  category = "categories"
  series = "series"
```

Related posts need Hugo's own related-content config. Without it, Hugo falls back to its default
index and results get noticeably worse:

```toml
[related]
  includeNewer = true
  threshold = 60
  toLower = true
  [[related.indices]]
    name = "tags"
    weight = 100
  [[related.indices]]
    name = "categories"
    weight = 200
```

---

## `params.runbook.*`

### Appearance

| Key | Type | Default | Effect |
|---|---|---|---|
| `themeMode` | string | `"auto"` | `auto` / `light` / `dark`. The pre-JavaScript default stamped on `<html data-theme>` |
| `showThemeToggle` | bool | `true` | Renders the theme toggle. It ships `hidden` and JavaScript unhides it |
| `accent` | string | `""` | Any CSS colour; empty uses the theme's own accent. **Not wired yet — see below** |
| `themeColor.light` | string | `"#ffffff"` | `<meta name="theme-color">` for the light palette. **Currently shadowed — see below** |
| `themeColor.dark` | string | `"#0d1117"` | `<meta name="theme-color">` for the dark palette. **Currently shadowed — see below** |
| `cspNonce` | string | `""` | Emitted on the inline theme guard and the font-override `<style>` for nonce-based CSP (ADR-4). See [Content Security Policy](#content-security-policy) |

`themeColor.*` are config rather than tokens because CSS custom properties are not readable from
`<head>`. **Keep them in sync with `--rb-color-bg` in `assets/css/tokens.css`;**
`scripts/check_contrast.py` asserts the theme's own literals still match, so the duplication cannot
rot silently.

> **Two honest caveats on this table, both verified against a build of `main`.**
>
> **`accent` does nothing today.** The key is declared in the root `hugo.toml` and read by no
> template and no stylesheet — `grep -rn accent layouts/` returns nothing. To recolour the accent
> right now, override the custom properties from
> [`hooks/custom-head.html`](extending.md) instead:
>
> ```html
> <style>:root{--rb-color-accent:#7c3aed;--rb-color-accent-hover:#6d28d9}
> :root[data-theme="dark"]{--rb-color-accent:#a78bfa;--rb-color-accent-hover:#c4b5fd}</style>
> ```
>
> If you do that, re-run `python3 scripts/check_contrast.py` against your values — the shipped gate
> only ever checks the shipped palettes.
>
> **`themeColor.*` is emitted but shadowed.** `head/seo.html` renders your values correctly, but
> `head/theme-guard.html` emits its own hard-coded `#ffffff` / `#0d1117` pair *earlier* in `<head>`,
> so a build currently carries **four** `<meta name="theme-color">` tags and the first pair wins.
> Setting these keys therefore has no visible effect until the duplicate is removed. Both files are
> owned by other workstreams; the fix belongs in their PRs, not in this document.

### Fonts

| Key | Type | Default | Effect |
|---|---|---|---|
| `bundledCodeFont` | bool | `true` | `false` falls back to the zero-byte system mono stack (REQ-FONT-2) |
| `codeFontLigatures` | bool | `false` | Off by default: ligatures misdraw `>=`, `!=`, `->` in shell |
| `bundledProseFont` | bool | `false` | Off by default: the system sans stack costs nothing |

### Content

| Key | Type | Default | Effect |
|---|---|---|---|
| `dateFormat` | string | `":date_long"` | Any `time.Format` layout or Hugo date token |
| `showReadingTime` | bool | `true` | Reading time in the byline |
| `showLastmod` | bool | `true` | "Updated" in the byline — only when `lastmod` is genuinely later than `date` |
| `showTerms` | bool | `true` | Tag and category chips at the foot of an article |
| `showPrevNext` | bool | `true` | Adjacent-post navigation, scoped to the section |
| `poweredBy` | bool | `true` | The "Built with Hugo" line in the footer |
| `externalLinksNewTab` | bool | `false` | `target="_blank"` on external links, plus a visually hidden "(opens in a new tab)" |
| `seriesTaxonomy` | string | `"series"` | Which registered taxonomy drives series navigation |
| `logo` | string | `""` | Publisher logo URL used in JSON-LD `publisher.logo` |

### Table of contents

| Key | Type | Default | Effect |
|---|---|---|---|
| `toc.enable` | bool | `true` | Site-wide switch; front matter `toc: false` overrides per page |
| `toc.minLevel` | int | `2` | Shallowest heading level included |
| `toc.maxLevel` | int | `3` | Deepest heading level included — set `4` for H4 |
| `toc.minHeadings` | int | `2` | Below this many in-range headings, no TOC is rendered at all |
| `toc.scrollSpy` | bool | `true` | Active-state tracking. The anchors work without it |

**Levels come from here, not from `markup.tableOfContents`.** Same reasoning as REQ-CB-1: the
consumer's `startLevel`/`endLevel` is site configuration, and a theme that reads it inherits
whatever the consumer happens to have. Runbook builds the list itself from `.Fragments`.

### Related posts

| Key | Type | Default | Effect |
|---|---|---|---|
| `related.enable` | bool | `true` | |
| `related.limit` | int | `5` | Maximum results |
| `related.fallback` | bool | `true` | When Hugo's related index returns nothing, show the most recent posts in the same section under a "Recent posts" heading instead of an empty block |

### Taxonomy

| Key | Type | Default | Effect |
|---|---|---|---|
| `taxonomyTitles` | map | `{}` | **REQ-TAX-1** — see below |
| `taxonomy.showCounts` | bool | `true` | Post count beside each term on the browse page |
| `taxonomy.rareThreshold` | int | `0` | Terms with **at most** this many posts move into a collapsed "Rarely used" `<details>`. `0` disables it |

### SEO

| Key | Type | Default | Effect |
|---|---|---|---|
| `seo.jsonLd` | bool | `true` | Emit JSON-LD at all |
| `seo.twitterSite` | string | `""` | `@handle` for `twitter:site` |
| `seo.robots` | string | `""` | Site-wide default robots directive; front matter `robots` overrides it |
| `seo.defaultImage` | string | `""` | Last-resort share image, after front-matter `image`/`cover` and a `{cover,feature,banner}.*` page resource |
| `author.name` | string | `""` | JSON-LD `author.name`. **Front-matter `author` wins over this**; if both are empty, a bare site-level `author` string, then the site title |
| `author.url` | string | `""` | JSON-LD `author.url` |

**Runbook never emits `<meta name="keywords">`** and never emits `articleBody` in JSON-LD. Both are
specified prohibitions ([003 §3.7](../specs/003-design-spec.md) items 2 and 3), not oversights.

### Search

| Key | Type | Default | Effect |
|---|---|---|---|
| `search.enable` | bool | `false` | Opt-in. Ships its own lazy chunk on `/search/` only (M4b) |

---

## Content Security Policy

Runbook emits **one inline `<script>`** and, only when you opt out of a font default, **up to two
inline `<style>` elements**. Everything else is an external, fingerprinted, SRI-tagged asset from
your own origin. There are no third-party hosts.

The inline script is the no-flash theme guard required by
[ADR-4](../specs/006-architecture-decisions.md): it stamps `data-theme` from `localStorage` before
first paint. It is the only blocking script on the page and it does exactly that one job.

### Option 1 — a nonce (recommended)

```toml
[params.runbook]
  cspNonce = "..."   # per-response value from your server or edge function
```

The value is emitted as `nonce="…"` on the guard and on both font-override `<style>` elements.

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...'; style-src 'self' 'nonce-...'
```

A nonce must be **unpredictable and different on every response** to be worth anything, which means
it cannot come from a static config file on a statically hosted site. Setting `cspNonce` to a
constant in `hugo.toml` is not a nonce; it is a fixed string an attacker can read from the page. Use
this path when a server, a reverse proxy or an edge worker injects the value at request time.

**A nonce needs no coordination with a Runbook release.** That is the whole reason to prefer it.

### Option 2 — a hash

For a purely static host, hash the inline content instead. **You must compute the hashes from
your own build output**, for the reason in the warning below.

Current values for the theme as it stands:

| Emitted by | Build | `script-src` / `style-src` value |
|---|---|---|
| Theme guard | `hugo` (no `--minify`) | `'sha256-GytWXkQmO8lO9yfkf/nGk5uKoncvdhsJM4S8wnPhTUQ='` |
| Theme guard | `hugo --minify`, Hugo 0.164.0 | `'sha256-066EEot1y+rU3UxWvORvUu09DDzZWH14UI7lqCCoGn8='` |
| `bundledCodeFont = false` style | `hugo` (no `--minify`) | `'sha256-v3bE38rd91/dWA2UYH0JTHtk4uL9KcbWxpLu0YR9vdU='` |
| `codeFontLigatures = true` style | `hugo` (no `--minify`) | `'sha256-/qQRSriaXpVVW/ltzkpq9C4PAFeRGJA8xC+Jozkoa68='` |

The two `<style>` hashes are needed **only if you changed those font defaults**; on the defaults
neither element is emitted at all.

> **The hash is not a property of the theme alone — it is a property of your build.** `hugo --minify`
> runs the HTML minifier over the inline script and rewrites it: on Hugo 0.164.0 the guard comes out
> as `…var e=localStorage…(e==="light"||…)&&(…)…}catch{}})()`, a different byte string from the
> template source and therefore a different hash. The minifier is a Go dependency of Hugo, so its
> output can also change between Hugo versions without a single line of Runbook changing.
>
> **Consequence: never copy a hash out of a document — generate it from the artefact you deploy,**
> in the same job that deploys it. The table above is a cross-check, not a source of truth.

Generate it from your own build:

```sh
python3 - <<'EOF'
import re, hashlib, base64, pathlib
html = pathlib.Path('public/index.html').read_text()
for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', html, re.S):
    body = m.group(1)
    if 'localStorage' not in body:          # skip the JSON-LD data blocks
        continue
    digest = hashlib.sha256(body.encode()).digest()
    print("script-src 'sha256-" + base64.b64encode(digest).decode() + "'")
EOF
```

Add `--minify` to the `hugo` command in your deploy job and to nothing else, then run the snippet
against that output, and the value is right by construction.

### If you allow neither

Set `themeMode` to `"light"` or `"dark"` rather than `"auto"` and accept that a reader's stored
choice is applied by the deferred `js/modules/theme.js` *after* first paint, i.e. a visible flash on
navigation for anyone whose choice differs from the configured default. Nothing else in the theme
breaks: the CSS is already correct for all three states before any script runs, so the guard only
ever *changes* the answer.

### The rest of the policy

`script-src 'self'` and `style-src 'self'` cover the fingerprinted bundles. Runbook adds:

| Directive | Why |
|---|---|
| `font-src 'self'` | Only if `bundledCodeFont` is on; the WOFF2 is served from your origin |
| `img-src 'self' data:` | The copy/copied/wrap icons are `data:image/svg+xml` **mask** URLs inside `assets/css/code.css`. A resource fetched by a CSS property is still an image fetch, so `data:` is required — without it the buttons paint as plain squares. There is no setting that turns these off |
| `connect-src 'self'` | Only if `search.enable` is on — the search chunk fetches its index from your origin |

No `frame-src`, no `child-src`, no third-party origin is needed by the theme itself. Anything you add
through the [override hooks](extending.md) is yours to allow.

---

## REQ-TAX-1 — term titles

Hugo derives a term's title from its key by capitalising each hyphen-separated segment. For the
normal kebab-case convention that produces the wrong string in the `<title>`, the `<h1>`, every
breadcrumb, every tag chip and the JSON-LD `keywords`:

| Term | Hugo renders | Should be |
|---|---|---|
| `amazon-eks` | Amazon-Eks | Amazon EKS |
| `sql-server` | Sql-Server | SQL Server |
| `github-actions` | Github-Actions | GitHub Actions |
| `ci-cd` | Ci-Cd | CI/CD |
| `infrastructure-as-code` | Infrastructure-as-Code | Infrastructure as Code |

Runbook resolves it in `layouts/_partials/utils/term-title.html`, in this order:

1. **the term's own `_index.md` front-matter `title`** — always wins;
2. **`params.runbook.taxonomyTitles[<url segment>]`**;
3. hyphens and underscores → spaces, title-cased.

Step 3 alone already fixes most of them, including `infrastructure-as-code`, so **the map only
needs entries for capitalisation that cannot be inferred**:

```toml
[params.runbook.taxonomyTitles]
  "amazon-eks" = "Amazon EKS"
  "ci-cd" = "CI/CD"
  "github-actions" = "GitHub Actions"
  "sql-server" = "SQL Server"
  "cert-manager" = "cert-manager"
```

Keys are the term's **URL segment**, lower-case. Hugo lower-cases TOML keys, so the casing you write
does not matter.

The reference site accumulated **83 taxonomy `_index.md` files, 60 of which exist solely to override
a display title**. This replaces all 60. **A site with zero `_index.md` files renders correctly.**

Step 3 honours the site's `titleCaseStyle`; the AP default is what turns `infrastructure-as-code`
into "Infrastructure as Code" rather than "Infrastructure As Code".

## REQ-TAX-2 — retiring a term is a file deletion

**A term's `_index.md` keeps its page building even when no post carries the term.** Removing a tag
from every post therefore leaves an orphaned page listing nothing, not the redirect you intended.
This was hit for real on the reference site (citizix#72).

To retire or merge a term:

1. remove it from the front matter of every post;
2. **delete the term's `_index.md`** — this is the step everyone misses;
3. put the redirect on the **surviving** term's `_index.md` as an `aliases` entry:

```yaml
# content/tags/kubernetes/_index.md
---
title: "Kubernetes"
aliases:
  - /tags/k8s/
---
```

The theme cannot prevent this, which is why it renders a real "No posts currently carry this term"
state instead of a blank page: if you see it, you have an orphan.

---

## Front matter

The schema below **is** [`archetypes/default.md`](../archetypes/default.md) — `hugo new
posts/my-post.md` produces exactly these keys, with the reasoning for each in comments. Nothing here
is invented for the documentation.

| Key | Type | In the archetype | Effect |
|---|---|---|---|
| `title` | string | yes | The `<h1>`, `<title>`, JSON-LD `headline` |
| `date` | date | yes | Byline, JSON-LD `datePublished`, sort order. Absent is handled everywhere and never prints "Invalid date" — the archive groups undated posts under a real "Undated" heading rather than Go's zero year |
| `draft` | bool | yes | Hugo's own; excluded from the build unless `--buildDrafts` |
| `description` | string | yes | Meta description, OG/Twitter description, JSON-LD `description`, list summary. Falls back to Hugo's generated summary, which for a procedure is the first 70 words of the preamble |
| `tags`, `categories` | list | yes | Chips, `article:tag`, JSON-LD `keywords` / `articleSection` |
| `image` | string | commented | Share image. Page resource name, path under `assets/`, or absolute URL. **Never a layout assumption** (ADR-7) |
| `series` | list | commented | Series navigation. Requires the consumer to register the taxonomy — a theme cannot |
| `toc` | bool | commented | Per-page override of `params.runbook.toc.enable` |
| `robots` | string | commented | Per-page robots directive; overrides `params.runbook.seo.robots` |
| `lastmod` | date | commented | "Updated" in the byline and JSON-LD `dateModified` — **only when genuinely later than `date`** |
| `cover` | string | no | Share image, checked after `image`. Supported for migrating content |
| `author` | string | no | JSON-LD `author.name` when `params.runbook.author.name` is unset |
| `weight` | int | no | Explicit series reading order; otherwise date ascending |
| `layout` | string | no | `"archive"` selects the archive template — see [Special pages](#special-pages) |
| `aliases` | list | no | Hugo's own; the redirect mechanism REQ-TAX-2 relies on |

`open` is read by the `details` shortcode from its own parameters, not from page front matter.

### Per-page override precedence

Only these keys override site configuration on a single page. Everything else in
`params.runbook.*` is site-wide.

| Front matter | Overrides | Resolution |
|---|---|---|
| `toc: false` / `toc: true` | `params.runbook.toc.enable` | Probed with `isset`, so `toc: false` is honoured. The `minLevel`/`maxLevel`/`minHeadings` thresholds still apply, so a page can still end up with no TOC because it has too few headings |
| `robots` | `params.runbook.seo.robots` | Page value wins when non-empty |
| `image`, then `cover` | `params.runbook.seo.defaultImage` | `image` → `cover` → a page resource matching `{cover,feature,banner}.*` → `seo.defaultImage`. Each name is resolved as a page resource, then as an asset, then treated as an absolute URL |
| `author` | `params.runbook.author.name` | **Front matter wins**, then `author.name`, then a bare site-level `author` string, then the site title. A list in front matter uses its first entry |
| a term's `_index.md` `title` | `params.runbook.taxonomyTitles[<segment>]` | Front matter always wins — see [REQ-TAX-1](#req-tax-1--term-titles) |
| `layout: "archive"` | — | Template selection, not a setting |

**Spelling note.** These are read from the page's own front matter and are *not* namespaced under
`runbook`. That is deliberate: `toc`, `image` and `cover` are the keys `hugo-theme-stack` uses, and
migrating content should not have to be rewritten.

## Special pages

### Archive

Hugo has no "archive" page kind, so the template is selected by front matter:

```yaml
# content/archive/_index.md
---
title: "Archive"
layout: "archive"
---
```

Every post in `mainSections`, grouped by year, unpaginated on purpose so browser find-in-page
works across the whole archive.

### Main sections

`mainSections` is Hugo's own setting and Runbook never hard-codes `post`:

```toml
[params]
  mainSections = ["posts"]
```

Hugo populates it automatically from the section with the most pages when it is unset, so this
works untouched on most sites.

---

## Migrating from `hugo-theme-stack`

| Stack | Runbook |
|---|---|
| front matter `image` | supported unchanged — used for OG, Twitter and JSON-LD, never for layout (ADR-7) |
| front matter `toc: false` | supported unchanged |
| `[params] mainSections` | supported unchanged |
| `<meta name="keywords">` | **dropped deliberately** — ignored since 2009, and Bing treats it as a spam signal |
| per-page inline admonition CSS | dropped — the styling is in the budgeted main stylesheet |
| widget/sidebar config | no equivalent; Runbook's sidebar is the table of contents |

`markup.highlight.lineNos` and `lineNumbersInTable` can be left as they are: the render hook
ignores them. Setting them to `false` anyway is still worth doing, as a trap for anyone who later
bypasses the hook (specs/010 §3).

A fuller migration guide — URL and alias parity, the ten local override files, the RSS and sitemap
diff — is `docs/migration.md`, owned by the citizix-migration workstream. It is not in the tree yet.

---

## Coverage and gaps

**Read this before concluding a key is missing.** Runbook is pre-release and four workstreams are
merging in parallel ([contracts §0](contracts.md#0-round-2--the-current-split)), so a reference that
silently omits three settings is worse than one that names them.

### Verified complete, as of 2026-07-28

Every key documented above was cross-checked three ways: against the `[params.runbook]` block in the
repo-root [`hugo.toml`](../hugo.toml), against the resolver in
`layouts/_partials/utils/settings.html`, and against every `site.Params.runbook` / `$rb.` read in
`layouts/`. The three sets agree, with the exceptions called out in the Appearance section
(`accent` is declared and unread; `themeColor.*` is read but shadowed by a duplicate `<meta>`).

That covers, by group: Appearance (6), Fonts (3), Content (9), Table of contents (5), Related posts
(3), Taxonomy (3), SEO (6), Search (1) — **36 keys** — plus the 15 front-matter keys, the four
consuming-site requirements (`markup.highlight.noClasses`, `[taxonomies]`, `[related]`,
`mainSections`), and Content Security Policy.

### Keys not yet documented here, and why

| Area | State |
|---|---|
| **Search** (`params.runbook.search.*` beyond `enable`) | **Arrived too late for this pass.** The client-side search workstream had not pushed a branch or opened a PR when this was written. `search.enable` is the only search key that exists in the tree today; index fields, result limits and placeholder text will arrive with `docs/search.md` and must be folded in here |
| **Shortcodes** | **Checked, and there is nothing to fold in.** Branch `eutychus/m4b-shortcodes` (commit `cfde4ae`, no PR open at the time of writing) adds the `tabs`/`tab` shortcodes, `docs/shortcodes.md` and six `i18n` strings, and introduces **no new `params.runbook.*` key** — it only consumes the existing `seriesTaxonomy`. Shortcode *arguments* are documented in `docs/shortcodes.md`, not here. Re-check when it merges |
| **Migration** | **Arrived too late for this pass.** No branch existed when this was written. `docs/migration.md` may introduce compatibility settings for a Stack-to-Runbook move; none exist in the tree yet |

The convention that keeps this honest is in [contracts §0](contracts.md#0-round-2--the-current-split):
a workstream adding a setting records it in **its own** doc and lists it in its PR body, and this
file folds it in. If you find a `params.runbook.*` key in the tree that is not in this document, that
is a bug in this document — please open an issue.
