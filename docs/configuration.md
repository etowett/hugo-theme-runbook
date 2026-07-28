# Configuration reference

**Status:** in force from M1. The complete annotated reference is an M5 deliverable
([008](../specs/008-milestones.md)); it starts here so it is never a retrofit.

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
| `accent` | string | `""` | Any CSS colour; empty uses the theme's own accent |
| `themeColor.light` | string | `"#ffffff"` | `<meta name="theme-color">` for the light palette |
| `themeColor.dark` | string | `"#0d1117"` | `<meta name="theme-color">` for the dark palette |
| `cspNonce` | string | `""` | Emitted on the inline theme guard for nonce-based CSP (ADR-4) |

`themeColor.*` are config rather than tokens because CSS custom properties are not readable from
`<head>`. **Keep them in sync with `--rb-bg` in `assets/css/tokens.css`.**

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
| `seo.defaultImage` | string | `""` | Fallback share image when a page has none |
| `author.name` | string | `""` | JSON-LD `author.name`; falls back to front matter `author`, then a bare site-level `author`, then the site title |
| `author.url` | string | `""` | JSON-LD `author.url` |

**Runbook never emits `<meta name="keywords">`** and never emits `articleBody` in JSON-LD. Both are
specified prohibitions ([003 §3.7](../specs/003-design-spec.md) items 2 and 3), not oversights.

### Search

| Key | Type | Default | Effect |
|---|---|---|---|
| `search.enable` | bool | `false` | Opt-in. Ships its own lazy chunk on `/search/` only (M4b) |

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

Matches [`archetypes/default.md`](../archetypes/default.md).

| Key | Type | Effect |
|---|---|---|
| `title` | string | The `<h1>`, `<title>`, JSON-LD `headline` |
| `date` | date | Byline, JSON-LD `datePublished`, sort order. Absent is handled everywhere and never prints "Invalid date" |
| `lastmod` | date | "Updated" in the byline and JSON-LD `dateModified` — **only when later than `date`** |
| `description` | string | Meta description, OG/Twitter description, JSON-LD `description`, list summary |
| `tags`, `categories` | list | Chips, `article:tag`, JSON-LD `keywords` / `articleSection` |
| `series` | list | Series navigation. Requires the taxonomy to be registered |
| `weight` | int | Explicit series reading order; otherwise date ascending |
| `image` | string | Share image. Page resource name, path under `assets/`, or absolute URL |
| `cover` | string | Same, checked after `image` |
| `toc` | bool | Per-page override of `params.runbook.toc.enable` |
| `robots` | string | Per-page robots directive |
| `layout` | string | `"archive"` selects the archive template — see below |

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
