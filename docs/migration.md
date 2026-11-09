# Migrating from hugo-theme-stack to Runbook

**Owner:** the citizix migration parity workstream ([contracts §0](contracts.md#0-round-2--the-current-split)).
**Spec:** [010 — citizix migration](../specs/010-citizix-migration.md), with the verification
plan in [007 §2 Layer 2](../specs/007-verification.md) and the budgets in
[005](../specs/005-performance-budgets.md).

Everything below was **measured**, not reasoned about: the reference archive
(citizix.com — 500 posts, 8,907 fenced code blocks, 1,154 pages) was built with
hugo-theme-stack v4.0.3 and then with Runbook at the same content commit, and the two
builds were diffed URL by URL. Numbers in this document come from that pair of builds:
Hugo v0.164.0+extended, citizix content at `dc1b321`.

Reproduce any of it with the commands in §10.

**Doing the cutover rather than reading about it: §12.** That section is the executable
form of [010](../specs/010-citizix-migration.md) §5 — the preview recipe, the fixture set
to compare by eye, the rollback triggers and the rollback command. Read it before the day.

---

## 1. What actually breaks

Almost nothing, and the *almost* is specific.

**Post URLs are theme-independent.** All 482 post files pin their own `url:` in front
matter, and a theme cannot change front matter. The configured `permalinks.post` is
never consulted. So the check most people would run — "do the article URLs match?" —
passes trivially and proves nothing.

**All 356 aliases on the Stack build are theme-independent.** 328 are the automatic
`/page/1/` paginator aliases that any theme regenerates; 26 are term-merge redirects that
live in taxonomy `_index.md` front matter; the last two, `/about/` and `/about-citizix/`,
are page front matter. The only aliases Runbook does not reproduce are paginator aliases
for pages it does not paginate — the 2 taxonomy browse pages (§4) and 10 empty tags (below).

What the theme genuinely controls, and what the manifest diff found:

| Surface | Result |
|---|---|
| Post, page, section, term URLs | **identical** |
| Home and section pagination `/post/page/{n}/` | **identical** |
| `/search/` | **still exists**, HTML + RSS + JSON |
| RSS feed paths (329 feeds) | **identical** |
| Canonical, `og:url` | **identical on every page that still exists** |
| `/tags/page/{n}/`, `/categories/page/{n}/` | **31 URLs removed** — §4 |
| JSON-LD `mainEntityOfPage` | **identical**. At `9ec479a` Runbook dropped it from 4 non-article pages that Stack typed as `Article`; citizix#131 then stopped typing them `Article` upstream, so the two now agree |
| RSS item lists | **2 feeds differ** — both by design, §9 |
| `/tags/{t}/page/1/` aliases | **10 removed**, all on tags with an `_index.md` and zero posts. A **citizix defect**: delete the ten orphan term files |
| Sitemap `<loc>` | **189 thin-term URLs added**, 2 `<image:loc>` entries dropped — §5. The 189 are a **Runbook gap**, #122 |

Totals: **298 differences across 8 causes, 0 unreviewed** — two of the eight are recorded
as `defect: true`, to be deleted when their fix lands rather than kept as design. The
reasoning for each is recorded in `.github/parity/reviewed-differences.json`, where the
reason field is structurally mandatory.

Measured at citizix@`c98c01b`, Hugo v0.169.0+extended (#61), superseding `9ec479a`. The
file records the ref it was derived at, because a reviewed difference is only true of the
content commit it was reviewed against.

---

## 2. Configuration

### 2.1 The `markup.highlight` cleanup — do this, even though it does not matter

Set both to `false` in your own config as part of cutover:

```yaml
markup:
  highlight:
    lineNos: false
    lineNumbersInTable: false
    noClasses: false          # required: Runbook ships two class-based palettes (ADR-2)
```

Runbook is correct either way. `layouts/_markup/render-codeblock.html` builds its own
option set and passes every structure-changing key on **every** call, so the site's
line-number configuration cannot leak into theme output (REQ-CB-1,
[004](../specs/004-hugo-mechanics.md) §2). This was verified at archive scale, not on a
fixture: the whole 1,058-page build is **byte-identical** with and without

```bash
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true
```

and emits **zero** `<table class="lntable">` in either run.

Fix the config anyway. Leaving it wrong is a trap for whoever later writes a template
that calls `transform.Highlight` without the hook.

### 2.2 `guessSyntax: true` changes what gets highlighted

`guessSyntax` is on the structure-changing list, so the hook forces it **off**. On this
archive that moved **183 blocks across 117 pages** out of Chroma and into a plain
`<pre><code class="language-conf">`.

That is a correction. With `guessSyntax: true`, Chroma guessed lexers named
`fallback` and **`gdscript3`** for nginx-style config files and coloured them
accordingly. Wrong colours on a config file are worse than none.

The blocks are not left bare: the render hook fires on all **8,907** fenced blocks —
exactly the number of Chroma blocks Stack produced — so every one of the 183 still gets
the Runbook frame, the language tag, the copy button and the wrap toggle. Only the
syntax colouring is gone, because Chroma has no lexer for `conf`
([verification §6](verification.md#finding-an-unknown-lexer-produces-a-different-dom)).

### 2.3 Setting map

| Stack | Runbook | Note |
|---|---|---|
| `params.article.toc: true` | `params.runbook.toc.enable` | levels from `params.runbook.toc.minLevel`/`maxLevel`, **not** from `markup.tableOfContents` |
| `params.article.readingTime` | `params.runbook.showReadingTime` | |
| `params.colorScheme.default` | `params.runbook.themeMode` | `auto` / `light` / `dark` |
| `params.colorScheme.toggle` | `params.runbook.showThemeToggle` | |
| `params.dateFormat.published` | `params.runbook.dateFormat` | |
| `params.sidebar.*`, `params.widgets.*` | — | Runbook has no sidebar and no widget system |
| `params.featuredImageField: image` | — | Runbook reads `image` then `cover` from front matter directly (ADR-7) |
| `params.defaultImage.opengraph.src` | `params.runbook.seo.defaultImage` | |
| `params.opengraph.twitter.site` | `params.runbook.seo.twitterSite` | |
| `params.author.*` | `params.runbook.author.name` / `.url` | |
| `params.comments.*` | — | §6 — Runbook ships no comment provider |
| `params.rssFullContent: true` | — | Runbook's RSS is full-content unconditionally; cap with `services.rss.limit` |
| `module.mounts` for the Stack theme | — | delete; on this site the content mount pointed at a directory that does not exist |
| `related` | `related` | unchanged, Hugo-native |
| `locale: en-us` | — | see §7 |

Every Runbook setting is namespaced under `params.runbook` (contracts §2.4) so it can
never collide with your own keys. Reference: [configuration.md](configuration.md).

---

## 3. Front matter

| Stack key | Runbook | Behaviour |
|---|---|---|
| `image` | **supported unchanged** | `utils/page-image.html` reads `image` first, precisely so a Stack site needs no rewrite. Resolved as a page resource, then a global asset, then taken at face value and made absolute |
| `cover` | supported | second in the same resolution order |
| `toc: false` | **not implemented** | Stack's per-page TOC opt-out has no Runbook equivalent. `params.runbook.toc.enable` is site-wide only |
| `aliases` | unchanged | Hugo-native |
| `url`, `slug`, `date`, `lastmod`, `draft` | unchanged | Hugo-native |
| `categories`, `tags` | unchanged | |
| `keywords` | **ignored** | Runbook never emits `<meta name="keywords">` ([003](../specs/003-design-spec.md) §3.7 item 3). Leaving the front matter in place is harmless |
| `type: post` | unchanged | |
| `layout: search` | **matched by `layouts/search.html`** | shipped in #23; it does not fall through to `page.html` |
| `outputs: [html, rss, json]` | **keep all three** | see below |

**Keep `json`. Runbook's search index is built from it.** Under Hugo's post-v0.146
lookup, a root-level `search.json` matches `layout: search` + kind `page` + output
`json`, and Runbook has shipped [`layouts/search.json`](../layouts/search.json) since
#23 — so the archive's search page needs no front-matter change at all.

Earlier revisions of this section said the opposite: that Runbook shipped no JSON
template for a page kind and that `outputs: json` was therefore a hard build failure
under `--panicOnWarning`. That was true before #23 and false after it, and the
`layout: search` row directly above still described the search workstream as unshipped,
which is how the error survived. Building this archive with `json` left in place exits 0,
emits no `found no layout file` warning, and produces `/search/index.json` — 491
documents, 178,113 B at `9ec479a` (476 and 179,548 B at `c98c01b`), in Runbook's own `{"v":1,"docs":[…]}` schema, against the 4,617,791 B
of full article text Stack's index carries.

**Dropping `json` does not merely skip the index — it removes the search UI.**
`layouts/_partials/search/ui.html` gates the whole widget on the output format:

```go-html-template
{{- with .OutputFormats.Get "json" }}{{ $json = .RelPermalink }}{{ end -}}
{{- if and $cfg.enable $json -}}
```

With no `json` output there is no `$json`, so nothing renders. The incumbent theme
resolves its index the same way — `data-json` plus a client-side `fetch` — so the advice
to drop it broke search on **both** themes, which is what made it worth correcting
rather than merely tidying.

The parity harness carried the same mistake in executable form: it stripped `json` from
the search page and pinned `search.enable: false`, so no parity run ever built either the
index or the UI. Both are gone; `.github/parity/citizix-runbook.yaml` now sets
`search.enable: true`. Note that `scripts/check_parity.py` walks `.html` and `.xml` only,
so the index is invisible to the manifest diff on both sides and the diff was never going
to catch its absence — `.github/workflows/parity.yml` asserts the index separately, for
exactly that reason.

**Two content typos this survey found have since been fixed upstream** (citizix#84, in
the pinned ref): `latmod:` for `lastmod:` in `content/page/privacy-policy/index.md`, and
a capital `Keywords:` in
`content/post/2021-09-01-install-manjaro-21-gnome-step-by-step-with-screenshots.md`.
Neither spelling appears anywhere in the corpus at `9ec479a` or at `c98c01b`. Kept as a note because both
are silent — Hugo ignores an unknown front-matter key and lower-cases a known one — so
they are worth grepping for on any archive being migrated, not only this one.

---

## 4. URLs you must redirect

**31 URLs disappear**, all of them pagination on the taxonomy *browse* pages:

```
/tags/page/2/  …  /tags/page/30/          (29)
/categories/page/2/ , /categories/page/3/  (2)
```

plus the two `/page/1/` aliases Hugo mints for them.

The cause is a design decision, not a bug. Stack paginates `/tags/` at `pagerSize`,
which turns 295 tags into 30 pages of ten. Runbook's `taxonomy.html` renders **every**
term on one page, grouped by initial letter, alphabetised by *display* title and
counted, with rarely-used terms optionally folded into a `<details>`
([003](../specs/003-design-spec.md) §3.4). Half this archive's tags are used once;
paginating them into 30 near-identical pages is 30 URLs of noise for a reader and for a
crawler.

**Ship 301s for all 31 to `/tags/` and `/categories/` respectively.** They are in
Google's index today. Two ways:

- server-side, at whatever serves the site — for citizix, two lines of `static/_redirects`; or
- `aliases:` on `content/tags/_index.md` and `content/categories/_index.md`, which makes
  Hugo emit the meta-refresh stubs. Cheaper to review, worse for crawlers than a 301.

Prefer the server rule. For the reference archive it is **not yet in place**, and that is
deliberate: at the pinned ref it was an nginx `location` regex from citizix#86 (historical —
citizix@`8918b75` removed nginx when the site moved to Cloudflare), and on Cloudflare a
`_redirects` rule beats a file that still exists, so it cannot ship while Stack still builds
those pages. It lands with the cutover PR — the lines and the reasoning are in §12.2.

**Cost of the change, measured** at `c98c01b` (Apple gzip, `gzip -n -9`): `/tags/` grows
from 4,534 to 5,497 B gzipped (+21.2%) because it now carries all 295 terms on one page —
at `9ec479a` it was 4,544 to 5,496 B for 297. It replaces 30 HTTP
round-trips with one. Two caveats on that number — it is above the 6,000 B list-page
budget's older 5,205 B reading because the corpus gained terms, and before #64 the per-page
no-regression rule in `check_budgets.py` failed on it, because `--article-glob` swept `/tags/` in
as an article. Since #64 `/tags/` is not swept, because an `index.xml` sits beside it. See §9
defect 8.

### `/search/` and everything else

`/search/` still exists at the same path, still carries its menu entry, and still emits
HTML and RSS — plus JSON, which is Runbook's search index and is why §3 says to keep
`outputs: json` rather than drop it. Section pagination (`/post/page/{n}/`), home
pagination, all 331 RSS feed paths, the sitemap URL set and every canonical are
unchanged.

---

## 5. The override files, classified

citizix carries **fourteen** local layout overrides at `c98c01b` — [010](../specs/010-citizix-migration.md)
§3 lists ten and omits `layouts/_partials/head/head.html`, and three more arrived after
`9ec479a`: the Dart Sass stylesheet and the two one-`<h1>` fixes from citizix#131.

| File | Classification | Action |
|---|---|---|
| `layouts/_default/baseof.html` | **Runbook capability** | Delete. Runbook's `baseof.html` emits `lang` and `dir` — see §7 for the one value that changes |
| `layouts/home.html` | **Runbook capability** | Delete |
| `layouts/shortcodes/admonition.html` | **Runbook capability** | Delete. The shortcodes workstream owns the replacement; its CSS moves into the budgeted stylesheet instead of `<style>` in every page head — §9 |
| `layouts/_partials/head/head.html` | **Runbook capability** | Delete. It exists only to strip `<meta name="keywords">` from upstream Stack. Runbook never emits it |
| `layouts/partials/head/schema.html` | **Runbook capability** | Delete. `head/schema.html` builds one map, `jsonify`s it once and marks it `safeJS`, which is the pattern this file was rewritten to in citizix#62; Runbook additionally emits `BreadcrumbList` and types non-article pages correctly |
| `layouts/partials/head/custom.html` | **Extension hook** | Split. OG-image fallback → `params.runbook.seo.defaultImage`. Admonition `<style>` → delete with the shortcode. Anything left → `hooks/custom-head.html` |
| `layouts/partials/head/script.html` | **Extension hook** | → `hooks/custom-head.html`. AdSense, GTM and the Pinterest verification meta are site code with live IDs; the theme ships none |
| `layouts/partials/google-tag-manager-body.html` | **Extension hook** | → `hooks/custom-body-start.html`, which exists for exactly this `<noscript>` iframe |
| `layouts/_partials/article/components/photoswipe.html` | **Delete** | ADR-7. Zero body images in 500 posts; this is a lightbox with nothing to light |
| `layouts/_partials/helper/external.html` | **citizix-only** | Delete with photoswipe — it is the CDN-manifest loader photoswipe used, and nothing else calls it |
| `layouts/sitemap.xml` | **citizix-only**, except the thin-term filter | Delete — but not until #122 gives Runbook the thin-term filter it now carries. Reasoning below |
| `layouts/_partials/head/style.html` | **Delete** | Stack-only. It switches Stack's stylesheet from LibSass to Dart Sass because Hugo 0.169 warns on LibSass. Runbook has no Sass, so there is nothing to port. Until cutover the parity job installs Dart Sass for the Stack baseline, at the version citizix `build.sh` pins |
| `layouts/_partials/article/components/details.html` | **Runbook capability** | Delete. It makes a post's title its `<h1>` on Stack (citizix#131). Runbook emits exactly one `<h1>` on every one of the 1,033 non-alias HTML pages at `c98c01b`, `404.html` included, counted |
| `layouts/_partials/sidebar/left.html` | **Runbook capability** | Delete. The other half of citizix#131: it demotes Stack's site-name `<h1>` off the homepage. Same count |

The thin-term half of `head/custom.html` — `noindex, follow` on terms with fewer than three
posts, added after `9ec479a` — is **not** an extension-hook item: it belongs with the sitemap
filter it pairs with, in #122.

Of the fourteen, seven are Runbook capabilities outright; three collapse into ADR-8 hooks
that already exist in `layouts/_partials/hooks/`; four are deleted (two Stack- or
photoswipe-only, two citizix-only).
**No file needs to survive as a fork of a Runbook template**, which is the outcome the
hook set was designed for.

### The sitemap: citizix-only, and it should be deleted rather than ported

This was left as an open question in [010](../specs/010-citizix-migration.md) §3.
Measured against the build, the answer is clear.

The override does three things beyond Hugo's internal sitemap:

1. **`<changefreq>`.** Google [documented in 2023](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping)
   that it ignores `changefreq` entirely. Hugo removed it from its internal template for
   that reason. Re-adding it emits a hint nobody consumes on 1,154 URLs.
2. **`<priority>`.** Also ignored by Google, and the logic here is a proxy for recency
   (`< 720 h` → 0.8) that `<lastmod>` already carries accurately.
3. **The Google image-sitemap extension.** It keys on `.Params.image`, which **two
   pages in the entire 1,154-page build carry**. On one of those two it emits an empty
   `<image:title/>`, because `$.Title` inside `range .Data.Pages` resolves to the sitemap
   page, not the ranged page. So the feature fires twice and is half broken.

None of that is a theme capability. A theme-level image sitemap would need cover images
to be a layout assumption, and ADR-7 says the opposite. A consumer who genuinely runs an
image-heavy site can drop their own `layouts/sitemap.xml` into their site — Hugo lets a
site template win over a theme's, and that is the correct seam.

**Runbook should not ship a sitemap override for those three.** Hugo's internal sitemap
(`<loc>` + `<lastmod>`) is what this site should serve for them, and at `9ec479a` the
manifest diff confirmed the URL set was byte-for-byte the same.

**A fourth thing arrived after `9ec479a`, and it changes the answer.** citizix now leaves
terms with fewer than three posts out of the sitemap and marks them `noindex, follow`
(`layouts/partials/head/custom.html`), because Search Console showed about 70% of them
unindexed. That is not citizix-only: thin taxonomy pages are a property of any blog with
a long tail of tags. At `c98c01b` it is 189 URLs in Runbook's sitemap that are absent
from Stack's. So the override still goes, but the filter becomes a Runbook setting first —
**#122** — and until it lands the 189 are recorded as a `defect: true` difference rather
than as design. The `noindex` half is invisible to the manifest diff, which compares no
robots meta; #122 adds the assertion.

---

## 6. Comments, analytics and ads

**Runbook ships zero comment providers and zero analytics** (ADR-8, contracts §2.6).
On this archive that is 492 pages losing their Disqus block, so this is not optional
work — it is the one thing that will visibly disappear on cutover if it is skipped.

Disqus thread continuity is why a giscus-only theme was rejected
([006](../specs/006-architecture-decisions.md) Q5). The threads key on the page URL, and
post URLs are unchanged by this migration, so **every existing thread reattaches by
itself** once the embed is back.

Create `layouts/_partials/hooks/comments.html` **in the site**, not in the theme:

```go-html-template
{{- with site.Config.Services.Disqus.Shortname -}}
  {{ template "_internal/disqus.html" $ }}
{{- end -}}
```

`disqusShortname: citizix` in the site config stays exactly as it is. The copy-pasteable
version of this, and the giscus equivalent, are in
[extending.md](extending.md).

The other three, all site code with live IDs:

| What | Hook |
|---|---|
| GTM `<script>` + AdSense + Pinterest verification | `hooks/custom-head.html` |
| GTM `<noscript>` iframe | `hooks/custom-body-start.html` |
| Anything deferred | `hooks/custom-body-end.html` |

GA4 (`googleAnalytics: G-…`) is Hugo-native but Runbook does not call
`_internal/google_analytics.html` — it goes in `custom-head.html` too, or leave it to
GTM, which on this site already loads it.

> The demo site published to the Hugo Themes showcase is `exampleSite`, never citizix,
> precisely because of this section: the showcase forbids live tracking credentials
> ([009](../specs/009-showcase-compliance.md) §3).

---

## 7. `<html lang>` changes from `en-us` to `en`

Stack emits `lang="en-us"` from `site.LanguageCode`. Runbook emits `lang="en"` from
`site.Language.Lang`. `dir="ltr"` is unchanged.

This is deliberate and it cannot be fixed by configuration. Hugo v0.158.0 deprecated
`languageCode`, `.Language.LanguageCode` and `.Language.LanguageDirection`, and their
replacements (`locale`, `.Locale`, `.Direction`) **do not exist at the v0.146.0 floor**
Runbook declares. Either spelling breaks one end of the supported range, and CI builds
with `--panicOnWarning`, so a deprecation warning is a build failure
([contracts §3](contracts.md#deprecations-vs-the-version-floor)).

`en` is a valid BCP 47 language tag and a correct value for this content. If a regional
tag is genuinely required, set it per language:

```yaml
languages:
  en-us:
    weight: 1
```

which makes `site.Language.Lang` itself `en-us` at every supported Hugo version.

---

## 8. Taxonomy

### 8.1 REQ-TAX-1 — 83 `_index.md` files, 41 of which are pure noise

Stack has no display-title mechanism for terms, so citizix accumulated 82 term
`_index.md` files whose entire content is a `title:` line, added one at a time to stop
`/tags/amazon-eks/` rendering as "Amazon-Eks".

Runbook derives the title (hyphens → spaces, title-cased, honouring your
`titleCaseStyle`) and takes overrides from `params.runbook.taxonomyTitles`, keyed by URL
segment.

**Measured by rebuilding with the 60 title-only files deleted:** 41 of them produce an
identical title with no configuration at all. **19 need an entry**, and here is the
complete list for this archive:

```yaml
params:
  runbook:
    taxonomyTitles:
      almalinux-10: AlmaLinux 10
      amazon-eks: Amazon EKS
      centos-stream: CentOS Stream
      cert-manager: cert-manager
      digital-ocean: DigitalOcean
      github-actions: GitHub Actions
      github-pages: GitHub Pages
      hashicorp-vault: HashiCorp Vault
      ingress-nginx: ingress-nginx
      kube-state-metrics: kube-state-metrics
      multi-environment: Multi-Environment
      mysqld-exporter: mysqld Exporter
      nfs-kernel-server: NFS Kernel Server
      oauth2-proxy: OAuth2 Proxy
      open-webui: Open WebUI
      self-hosted: Self-Hosted
      site-to-site-vpn: Site-to-Site VPN
      sql-server: SQL Server
      wg-easy: wg-easy
```

> **Do not delete the other 22.** They carry `aliases:` — the redirects from the term
> consolidation in citizix#72 and #76 — and deleting the file deletes the redirect. Only
> the 60 title-only files are candidates, and only 41 of those are safe to remove
> outright.

### 8.2 REQ-TAX-2 — the trap when you merge terms

**A term's `_index.md` keeps its page building even when no post carries the term.**

Removing a tag from every post therefore leaves an orphaned term page listing nothing,
rather than the redirect you intended. Every consumer merging duplicate terms hits this,
and citizix did, in #72.

The fix has two halves and both are required:

1. **Delete the losing term's `_index.md`.** Without this the page keeps building at
   zero posts, and it is in your sitemap and your `/tags/` list.
2. **Put the redirect on the SURVIVING term**, as an `aliases:` entry:

   ```yaml
   # content/tags/kubernetes/_index.md
   ---
   title: Kubernetes
   aliases:
     - /tags/kubernetees/
     - /tags/k8s/
   ---
   ```

At `9ec479a` the build had **zero** zero-post term pages. At `c98c01b` it has **ten**, in both
themes — `/tags/{cloud-native,container-security,ingress-nginx,kubernetes-security,pod-security,production-deployment,rate-limiting,security-best-practices,security-hardening,self-hosted}/`.
citizix removed those tags from every post during its guide merges and left their title-only
`_index.md` files behind, so each still renders an empty page. That is the trap above in
reverse, and the fix is citizix-side: delete the ten files. The parity diff records it as a
`defect: true` alias difference until they go (§1). Both counts come from the
`numberOfItems` field Runbook writes into each term page's `CollectionPage` JSON-LD
(`grep -l '"numberOfItems":0' public/tags/*/index.html`), which is also the cheapest way to
check it on your own site.

---

## 9. Defects this migration found

Reported rather than fixed, because these files belong to other workstreams
(contracts §0) and a cross-boundary edit is a merge conflict. The one exception is
defect 3: a single line in `scripts/check_links.py`, which no round-2 workstream owns,
and which was failing the nightly job on `exampleSite` — that one is fixed here and
called out as such. Each defect below is reproducible with the commands in §10.

| # | Where | What |
|---|---|---|
| 1 | `layouts/rss.xml` | **FIXED in #25.** The home feed used `site.RegularPages` instead of filtering to `params.mainSections`, so `/about-us/`, `/contact-us/`, `/privacy-policy/` and `/search/` were published as feed items. At `9ec479a` both themes' `/index.xml` carried the same 491 items, and at `c98c01b` the same 476; the reviewed-difference rule that allowed it has been deleted |
| 2 | `layouts/rss.xml` | **FIXED in #25.** Ranged `.RegularPages`, which is **empty** on a taxonomy list kind, so `/tags/index.xml` and `/categories/index.xml` shipped as valid but empty channels. They now collect the pages carrying any term in the taxonomy. The two feeds still *differ* from Stack's, which list term pages rather than articles — that is a design difference and is recorded as one, no longer as a defect |
| 3 | `scripts/check_links.py` | **FIXED IN THIS CHANGE** (one line, in a file no running workstream owns). A heading id containing a non-ASCII character is emitted raw in `id=` and percent-encoded in `href=` — `id=step-3-—-optional-…` against `href=#step-3-%e2%80%94-optional-…`. That is not a theme bug: Go's `html/template` normalises URL-context attributes and `safeURL` does not suppress it, and a user agent percent-decodes a fragment before matching ids, so both spellings address the same element. The checker was comparing them raw. See below — this was **already failing on `exampleSite`**, not only on the archive |
| 4 | `scripts/check_budgets.py` | **FIXED in #64** — the shell fallback no longer picks an alias stub. `--article-glob` defaults to `posts/*/index.html`, which matches nothing on a site using flat `/:slug/` permalinks; the script then silently falls back to "the first page that matches", which on this archive is an **alias stub**, and reports the theme-shell CSS and JS as "not built yet". As found, the fallback should have skipped meta-refresh pages; it now skips them |
| 5 | `exampleSite/content/posts/image-and-figure.md` | References `/not-fetched.png`, which is not in the build. The only remaining `check_links.py` failure on `exampleSite` after defect 3 was fixed. Either the asset is missing or the fixture is deliberately testing a broken image, in which case it needs a recorded exclusion |
| 6 | citizix content | **FIXED UPSTREAM in citizix 49fdb91**, which every pin since `9ec479a` contains. `/production-grade-saltstack-multi-environment-gitops-almalinux-10/` linked to `#security-hardening`, which no heading on that page defined; it was pre-existing and failed on the Stack build too, so it was the archive's to fix rather than the theme's. At this pin the page carries neither the dangling `href` nor the `id`, and the first execution of the parity job (run 30436578455) reports no broken internal links, subresources or fragments across the whole build. `parity.yml` runs the link crawl **blocking** again as a result |
| 7 | `docs/verification.md` §2, §8 | Both say the internal link and fragment crawl "runs per PR". It does not — `ci.yml` runs only the REQ-CB-1, fixture, JSON-LD and budget gates. `check_links.py` runs in `scheduled.yml`, nightly |
| 8 | `scripts/check_budgets.py` | **FIXED in #64**; the `/search/` half was already fixed in #51. Alias stubs and list pages — any page with an `index.xml` beside it, so `tags/`, `categories/`, `page/`, `post/` and `search/` — are no longer swept as articles. Regular pages outside `mainSections`, such as `/about-us/`, still count as articles. As found: the per-page script-tag and no-regression rules are scoped by `--article-glob`, which on a flat `/:slug/` archive is `*/index.html` and therefore matches pages that are not articles. Two consequences at `9ec479a`, both of them intended behaviour reported as failures: `tags/index.html` trips the 2% no-regression rule at +21.0% (§4, and already a reviewed `url` difference), and `search/index.html` trips the 2-executable-script budget at 3 — the inline theme guard, `runbook.js`, and the lazily-loaded search chunk that the same script *also* budgets separately as `SEARCH_JS_GZ_MAX`. Counting that chunk twice means the gate contradicts itself on the one page that loads it. Same root cause as defect 4. `parity.yml` still runs the budget step `continue-on-error` for that reason; dropping it is a follow-up in that workflow, not a change to this document |

**Defect 3 was not a citizix problem.** Before the fix, `scripts/check_links.py` reported
**9 failures on `exampleSite` itself** — eight of them the Arabic headings in
`rtl-bidirectional-text.md`, which is the fixture that exists to catch exactly this class
of thing. Since `scheduled.yml` runs the crawl nightly against `exampleSite`, that job
was failing every night and opening a tracking issue for it. After the fix:
`exampleSite` 9 → 1, the archive 3 → 1, and the one that remains on the archive is
defect 6, which fails identically on the Stack build.

Non-defects worth knowing about:

- The 183 blocks that lose syntax colouring (§2.2) are the intended effect of forcing
  `guessSyntax: false`.
- `/tags/` growing 14.1% (§4) is the intended cost of not paginating it.

---

## 10. Reproducing it

The reference archive is a private repository, so this runs locally or through
`.github/workflows/parity.yml` (`workflow_dispatch`), never on a pull request.

```bash
# 0. Never build in the citizix checkout. Copy it.
SITE=$(mktemp -d)
cp -R ~/Code/my/citizix/{content,static,assets,archetypes,layouts,themes} "$SITE/"
cp ~/Code/my/citizix/config.yaml "$SITE/"

# 1. Baseline — Stack, at the SAME content commit as the comparison. A baseline
#    captured at a different commit measures the corpus changing, not the theme.
#    Since citizix's head/style.html override this needs Dart Sass on PATH, at the
#    version citizix build.sh pins (brew install sass/sass/sass).
hugo --source "$SITE" --destination /tmp/rb-parity/stack \
     --cleanDestinationDir --gc --minify

# 2. Candidate — Runbook. Apply the migration: drop the site's own layouts and rewrite
#    the config per §2. The search page's front matter is left ALONE — `outputs: json`
#    is what builds Runbook's index (§3).
RB=$(mktemp -d)
cp -R "$SITE"/{content,static,assets,archetypes} "$RB/"
# … write $RB/config.yaml per §2.3 …
hugo --source "$RB" \
     --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination /tmp/rb-parity/runbook \
     --cleanDestinationDir --gc --minify --panicOnWarning --printPathWarnings

# 3. The manifest diff. Exit 0 only when every difference is in the allowlist.
python3 scripts/check_parity.py /tmp/rb-parity/stack /tmp/rb-parity/runbook

# 4. Build-wide invariants. These two numbers are the pinned ref's, and
#    .github/workflows/parity.yml asserts the same pair — keep them in step.
python3 scripts/check_parity.py --audit /tmp/rb-parity/runbook \
        --expect-pages 1033 --expect-aliases 344

# 4b. The search index. check_parity.py walks .html and .xml only, so nothing above
#     would notice /search/index.json going missing (§3).
python3 -c "import json,sys; d=json.load(open('/tmp/rb-parity/runbook/search/index.json')); \
print(len(d['docs']), 'documents'); sys.exit(len(d['docs']) < 400)"

# 5. REQ-CB-1 at archive scale — these two trees must be byte-identical.
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true \
hugo --source "$RB" --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination /tmp/rb-parity/runbook-hostile --cleanDestinationDir --gc --minify
diff -rq /tmp/rb-parity/runbook /tmp/rb-parity/runbook-hostile

# 6. Page weights.
python3 scripts/check_budgets.py /tmp/rb-parity/stack --article-glob '*/index.html' \
        --write-baseline /tmp/rb-parity/stack-baseline.json
python3 scripts/check_budgets.py /tmp/rb-parity/runbook --article-glob '*/index.html' \
        --baseline /tmp/rb-parity/stack-baseline.json
```

---

## 11. What it costs the reader

Same content, same commit, same Hugo. Theme-shell figures are from one representative
article (`/how-to-install-and-configure-redis-6-on-ubuntu-20-04/`).

**The theme-shell rows were re-measured at `9ec479a`; the distribution table below was
re-derived on the runner at `c98c01b`.** Runbook's shell has grown since this section was written — CSS by 82% as the
shortcode and search stylesheets landed — and leaving the old figures would have
understated it. Stack's column reproduces byte-for-byte at both refs, which is what makes
the comparison sound: the movement is Runbook's, not the corpus's. The build-time row is
left at its original Linux-runner reading — swapping in a laptop number would compare two
machines rather than two themes.

| | Stack | Runbook |
|---|--:|--:|
| CSS, gzipped | 10,031 B | **7,354 B** |
| JavaScript, gzipped — core bundle | 2,800 B | **2,068 B** |
| JavaScript, gzipped — all chunks | 5,209 B | **3,484 B** |
| Search index, gzipped | 1,271,345 B | **41,296 B** |
| `<script>` tags on an article | 11 | **4** (2 executable + 2 `ld+json`) |
| Third-party hosts the theme adds | 5 | **0** |
| Build time, 1,154 pages (Linux runner, `dc1b321`) | 3,929 ms | 4,068 ms |

`7,354 B` of CSS sits against `check_budgets.py`'s 8,000 B ceiling with 646 B of
headroom — worth watching rather than acting on, but it is no longer the comfortable
margin the old 4,039 B figure implied.

The search rows are new because search was never built here before (§3). Runbook's index
is 178,113 B raw against Stack's 4,617,791 B — 26× smaller on the same 491 posts at
`9ec479a`; 179,548 B for 476 posts at `c98c01b` — and
that is a schema decision rather than a compression win. Stack stores the full `content`
of every article; Runbook stores five short keys per document (`t` title, `u` permalink,
`d` date, `s` a summary truncated at `summaryLength`, `g` taxonomy terms), which is what
`layouts/search.json` emits.

Page-weight distribution across the 479 pages that are articles in both builds, from
parity run [42674523402](https://github.com/etowett/hugo-theme-runbook/actions/runs/42674523402)
at `c98c01b` — GNU gzip on `ubuntu-latest`, both builds in the same job, so the movement is
the theme's and not the corpus's or the platform's. The figures are `check_budgets.py`'s
own; the rows it does not print come from the `budgets.json` and `stack-baseline.json` in
that run's `parity-manifests` artefact.

| | Stack | Runbook | |
|---|--:|--:|--:|
| p50 | 9,256 B gz | **7,180 B** | −22.4% |
| p90 | 12,441 B gz | **10,384 B** | −16.5% |
| max | 47,312 B gz | 48,112 B | +1.7% |
| homepage | 6,693 B gz | **5,101 B** | −23.8% |
| worst term page | 5,148 B gz | **4,518 B** | −12.2% |
| articles + term pages + homepage | 5.82 MiB | **4.46 MiB** | −23.4% |
| articles under 7 KB gz | 40 (8.4%) | **223 (46.6%)** | |

**Exactly one article of 479 gets heavier**, by 800 B (+1.7%) — the same page as at
`dc1b321`, the largest in the archive, where Runbook's per-block chrome on its code blocks
costs more than it saves. At `dc1b321` it was +138 B (+0.3%). It is inside
`check_budgets.py`'s 2% no-regression tolerance with **0.3 points to spare**, so the next
change to the code-block chrome is the one that fails the per-page rule, and it will fail on
this page first.

### 11.1 Enforced page-weight thresholds

The shipped values live in `PAGE_WEIGHT_THRESHOLDS` in
[`scripts/check_budgets.py`](../scripts/check_budgets.py). They are derived from the Runbook
column of the §11 table above — parity run 42674523402 at `c98c01b` — with uniform 5%
headroom rounded up. [Verification §4](verification.md#4-budgets-and-the-script-tag-decision)
records the four values and the re-pin procedure.

Enforcement belongs in `parity.yml`, where both builds use the same archive commit and GNU gzip
on the same runner. `ci.yml` reports the numbers only — synthetic fixtures do not represent
the archive. GNU gzip and Apple gzip disagree on identical bytes
([verification §1](verification.md#reproducibility)), so local measurements cannot replace
the runner's thresholds.

Re-derive the thresholds whenever `CITIZIX_REF` moves. Keep the per-page no-regression rule
alongside them — the distribution catches theme-wide growth, while the baseline catches the
individual article that gets heavier.

---

## 12. Cutover

[010](../specs/010-citizix-migration.md) §5 defines six steps. Steps 1 and 2 are done and are
§1 above. Steps 3 to 6 had no executable form at all, which is what this section is: the
preview recipe, the pages to compare by eye, the rollback triggers as numbers, and the
rollback command.

It is worth being blunt about why it is written down rather than improvised. Every other gate
in this repository exists because someone decided a green tick should mean something. The
cutover has no tick. It is a human procedure, so an unwritten procedure is the risk here, not
the theme. And the one step that has to work first time, on the day it is needed, under
pressure, is the rollback, which is also the only one that has never been run (§12.5).

**How citizix deploys now.** Since citizix@`8918b75` (2026-10-31) Cloudflare is connected to the
citizix repository and builds and serves the site itself: every push to `main` is a production
deploy, the build command is `./build.sh` with output directory `public`, and the Hugo version is
the `HUGO_VERSION` build variable in the Cloudflare dashboard (citizix `AGENTS.md`, `readme.md`
§Deploy). There is no deploy workflow, image or cluster any more. This section was first written
against the Docker → nginx → Kubernetes → Argo CD deploy that commit deleted, and
[010](../specs/010-citizix-migration.md) §5.5 then recorded manual `workflow_dispatch` deploys —
both historical. What that rule protected, that cutover is one deliberate human act, now lives in
the merge (§12.6). `TODO(eutychus): confirm whether the Cloudflare project is Pages or Workers —
citizix's own docs say "Workers/Pages" — and its project name.` This is **the Pages/Workers
TODO**: several platform questions below depend on it and point back here rather than re-asking.

Everything below is measured at citizix@`c98c01b`, the ref `.github/workflows/parity.yml` pins
since #61, unless it says otherwise; a row marked `9ec479a` is kept as the earlier pin's
reading. Deployment facts are read from citizix at `6d22b64`.

### 12.1 The preview, and how `noindex` is actually applied

The preview exists so that a person can compare it against production on the pages a manifest
diff cannot judge. It must not be indexed while that happens, and **three layers are involved,
because no single one covers the whole surface.**

**Layer 1 — the theme setting. This is the only layer Runbook ships.**
`params.runbook.seo.robots` is a site-wide default robots directive that front-matter `robots`
overrides ([configuration.md](configuration.md#seo)), and
[`layouts/_partials/head/seo.html`](../layouts/_partials/head/seo.html) emits it as
`<meta name="robots">`. It takes an environment variable, which is what makes it right for a
preview: the preview build then differs from the production build by one variable rather than
by a forked config file that drifts from the real one between now and cutover.

```bash
HUGO_PARAMS_RUNBOOK_SEO_ROBOTS="noindex, nofollow" hugo --source … --minify
```

On a git-connected Cloudflare build that variable has to be a **preview-only build variable**,
not a line in a branch: anything committed to the cutover branch reaches production when it
merges. `build.sh` passes `--environment production` on every build, preview or not, so a
`config/preview/` directory would never be read either. Whether the project can set a build variable for
preview deployments only (depends on the Pages/Workers TODO in §12).

**Measured on `exampleSite`, Hugo v0.164.0:** 34 of the build's 46 HTML files gain
`<meta name=robots content="noindex, nofollow">`. The 12 that do not are Hugo's own
meta-refresh alias stubs — the build reports `Aliases 12` — and each contains nothing but a
`<link rel=canonical>` and a `<meta http-equiv=refresh>`. **Hugo's internal alias template emits
no robots directive**, so this layer does not cover an alias stub, and it cannot cover
`/index.xml`, `/sitemap.xml` or `/search/index.json` at all, because none of those can carry a
`<meta>` tag. On the archive at `c98c01b` that is 344 alias stubs plus 329 feeds outside the directive.

**Layer 2 — `robots.txt`, which citizix already owns.** `static/robots.txt` is copied verbatim
into the build, so nothing a theme does can override it, and Hugo generates none of its own here
(`enableRobotsTXT` is not set in `config.yaml`). The production file ends `Allow: /` and
`Sitemap: https://citizix.com/sitemap.xml`. Deployed unchanged to a preview host, it invites
crawling and advertises production's sitemap. Ideally the preview serves its own — `User-agent: *`
/ `Disallow: /` — but a preview deployment is built from a branch, and there is one
`static/robots.txt` per branch: a `Disallow: /` committed to the cutover branch would de-index
production the moment it merges. So on Cloudflare this layer is the one to give up, not to fake,
and layer 3 carries the weight. `TODO(eutychus): confirm — or find a preview-only mechanism for
robots.txt that does not live in the branch.`

**Layer 3 — an `X-Robots-Tag` response header at the edge.** This is the only layer that reaches
every response: the alias stubs, the feeds, the sitemap and the search index included. On
Cloudflare it comes from one of two places, both citizix-side:

- **the platform's own preview behaviour** — whether Cloudflare adds an `X-Robots-Tag: noindex`
  to this project's preview URLs by default (depends on the Pages/Workers TODO in §12); the §12.3 edge check answers it in one
  `curl` either way; or
- **a `static/_headers` rule** — citizix has no `_headers` file today. An unscoped `/*` rule
  would ship `noindex` to production on merge, which is the worst failure this section can
  produce, so it is only usable if it can be scoped to the preview host. Whether `_headers` accepts a
  host-qualified pattern (depends on the Pages/Workers TODO in §12).

Layer 1 is still worth having even with layer 3 in place, because it survives being served from
somewhere other than that edge.

**What the preview must not change: `baseURL`.** `build.sh:26` hardcodes `-b https://citizix.com`,
so a preview built by `build.sh` emits production canonicals.
`TODO(eutychus): confirm non-production branch builds are enabled on the Cloudflare project and
run build.sh, and the preview URL form they get.` Leave `baseURL` alone. A canonical pointing at
production is the correct duplicate-content signal for a temporary copy, and the canonical
*values* are already asserted by `check_parity.py` in the parity job, so nothing is lost by not
re-deriving them against a preview host. Pointing it at the preview would buy nothing and would
make §1's canonical row unverifiable on the artefact you are about to ship.

**Disqus must be off on the preview.** §6's snippet lives in the *site*, and citizix's Disqus
shortname is a live account. Rendering the embed on a preview host registers new, empty threads
keyed on preview URLs, in the same account that holds years of real ones. Leave
`disqusShortname` unset on the preview build; an empty comment area on the preview is expected
and is not evidence of anything. There is no separate preview config any more — `config.yaml:31`
sets `disqusShortname: citizix` for every build — so, as with layer 1, this has to be a
preview-only build variable rather than a branch edit that would switch comments off in
production on merge. **Measured 2026-11-03** on a scratch copy of citizix at `6d22b64` (Stack,
Hugo v0.169.0, Dart Sass 1.107.1), built with `./build.sh` and nothing else changed: with
`HUGO_DISQUSSHORTNAME=` set empty, `grep -rl 'disqus\.com' public --include='*.html'` finds
**0** pages, against **480** without it. What remains is an empty `disqus-container` div and an
inert `DISQUS.reset` listener — no embed, no thread. Stack reads the shortname through Hugo's
internal `disqus.html`, from `site.Config.Services.Disqus.Shortname`, the same key the Runbook
snippet in [extending.md](extending.md#disqus) guards on, so the variable carries over — provided
the cutover config keeps the top-level `disqusShortname`. If it moves to
`services.disqus.shortname`, the variable becomes `HUGO_SERVICES_DISQUS_SHORTNAME`. Thread
continuity is verified on production after cutover — §12.7.

### 12.2 The fixture set to compare page-by-page

[010](../specs/010-citizix-migration.md) §5.3 says "the pinned fixture set" without saying which
pages. Reviewing 1,033 pages by eye is not a procedure, and reviewing a random 20 proves nothing.
These are the 21 URLs chosen at `9ec479a` — at `c98c01b`, one is replaced by its redirect and a
build-wide check, below; all of the others still build, checked against the Runbook build at
that pin — where something in this document says the theme changes behaviour, so each
one is in the list because a named section predicts what it should look like. Open each on the
preview and on production side by side.

| URL | What it is here to catch |
|---|---|
| `/` | Home. Carries `image: /og-default.png` (`content/_index.md`), so it is one of the two pages the retired sitemap image extension fired on — §5 |
| `/page/2/` | Home pagination survives — §4 |
| `/post/page/2/` | Section pagination survives — §4 |
| `/how-to-install-and-configure-redis-6-on-ubuntu-20-04/` | The representative article §11's theme-shell figures are read from |
| `/kubernetes-tls-security-hardening-guide-traefik-nginx/` | The largest page in the archive at 48,112 B gz on Runbook (47,312 B on Stack), and the **one article of 479 that gets heavier** under Runbook (+800 B, +1.7%, 0.3 points inside the 2% tolerance) — §11 |
| `/how-to-install-and-configure-puppet-7-server-on-ubuntu-20-04/` | [010](../specs/010-citizix-migration.md) §1 bug 1 — everything after the unterminated fence used to render inside a single code block |
| `/how-to-install-and-configure-postgres-13-on-centos-8/` | **`9ec479a` only.** §1 bug 2 — the last bare `<pre><code>` in the entire build. The page no longer exists on current citizix (citizix `3232d98`, #137) |
| `/how-to-install-and-configure-postgres-13-on-centos-8/` → 301 | Current citizix: must **301 to `/how-to-install-and-configure-postgres-17-on-rocky-alma-linux-9/`** (`static/_redirects`), on both themes |
| *(build-wide)* bare `<pre><code>` | §1 bug 2 on current citizix. No page exercises it any more: the Stack build at `6d22b64` has **0** pages containing a bare `<pre><code>`, and so do both builds at `c98c01b`. Check the Runbook rebuild stays at 0 — `grep -rl '<pre><code>' public --include='*.html'` |
| `/production-grade-saltstack-multi-environment-gitops-almalinux-10/` | §9 defect 6. It must still fail **identically** on both themes, not differently |
| `/how-to-secure-kubernetes-clusters-with-firewalld-and-saltstack-almalinux-10-production-ready/` | The only post using the `admonition` shortcode — §5's replacement, and the page that proves the admonition CSS moved out of the per-page `<style>` |
| `/install-manjaro-21-gnome-step-by-step-with-screenshots/` | `image: /android-chrome-512x512.png` — the second image-sitemap page, and the OG-image path — §5 |
| `/tags/` | §4 — unpaginated, all 297 terms, 4,544 → 5,496 B gz |
| `/categories/` | §4 — same change, 28 terms |
| `/tags/page/2/` | Must **301 to `/tags/`**, and `/categories/page/2/` to `/categories/`. That redirect is `static/_redirects`, not the theme, so the manifest diff cannot see it — and it is not there yet; see below |
| `/tags/amazon-eks/` | REQ-TAX-1 — a term whose title comes from `params.runbook.taxonomyTitles` rather than from an `_index.md` |
| `/tags/k8s---docker/` | REQ-TAX-2 — a retired term whose redirect lives as `aliases:` on the surviving `/tags/k8s/`. Deleting the wrong file breaks this silently — §8.2 |
| `/search/` | §3 — the page, the UI, and the widget's dependence on `outputs: json` |
| `/search/index.json` | §3 — 476 documents at `c98c01b`. `check_parity.py` walks `.html` and `.xml` only, so nothing in the manifest diff would notice it missing |
| `/about-us/` | §5 — **`9ec479a` only:** one of the four pages that lost `mainEntityOfPage` and gained `@type WebPage`; at `c98c01b` both themes type it `WebPage` (§1). It carries the archive's only page `aliases:` — three declared, one of them its own URL, so two alias stubs, `/about/` and `/about-citizix/` — §1 |
| `/privacy-policy/` | The same `9ec479a`-only JSON-LD change, plus the `latmod:` typo fix that landed upstream — §3 |
| `/index.xml` | §9 defects 1 and 2 — the home feed, 476 items at `c98c01b`, no `/about-us/` |
| `/sitemap.xml` | §5 — the override is deleted, and Hugo's internal sitemap must produce the same `<loc>` set **except** the 189 thin terms (808 against 621 at `c98c01b`) until #122 lands |

`/contact-us/` is deliberately absent: it changes in exactly the same way as `/about-us/` and
`/privacy-policy/`, and a fixture set nobody finishes is worse than a shorter one.

**The taxonomy-pagination 301s must be restored in the cutover PR.** They used to be two regex
`location` blocks in nginx (historical — removed with nginx in citizix@`8918b75`). citizix#124
moved them to `static/_redirects` during its review and dropped them before merge, deliberately:
Stack still builds and links `/tags/page/N/`, and on Cloudflare a `_redirects` rule beats a file
that exists, so shipping them before the theme changes would strand those pages. So they belong
in the same PR as the theme switch, which also means a revert of that PR removes them again
(§12.5). `static/_redirects` takes splats and placeholders, not regex (citizix `AGENTS.md`), so
the two lines are:

```text
/tags/page/* /tags/ 301
/categories/page/* /categories/ 301
```

The splat is wider than the old `[0-9]+`, which is harmless — nothing else lives under
`/tags/page/` — and it still cannot match per-term pagination such as `/tags/kubernetes/page/2/`,
which Runbook keeps.

**One fixture has moved since `9ec479a`.** The PostgreSQL 13 post was retired in citizix#137, so
its row is kept for the pinned ref only, the redirect gets a row of its own, and §1 bug 2 is
checked build-wide instead of on a page.

### 12.3 Checking the preview — what is automated and what is not

[010](../specs/010-citizix-migration.md) §5.4 asks for the link crawl and the budget gates
against the preview. **Neither `scripts/check_links.py` nor `scripts/check_budgets.py` was taught
to speak HTTP, and that is a decision rather than an omission.** Both want a *tree*. While citizix
shipped a Docker image, the tree was extracted from the image that was actually deployed
(historical). Cloudflare keeps its build output to itself, so the tree now comes from **running
`build.sh` locally at the commit the preview deployment was built from.**

**Label it for what it is: a local rebuild, not the served artefact.** It is the same script at
the same commit, but it is only the same bytes if the inputs match, so record them next to the
results — the deployment's commit, `hugo version`, and `sass --version`. The last one is not
pedantry: `build.sh` downloads its pinned `DART_SASS_VERSION` only when no `sass` is on `PATH`,
so a laptop with Homebrew's Sass builds the stylesheet with whatever version that is. The edge
checks below are the evidence for what is actually served; the rebuild is the evidence for what
the gates say about it.

```bash
# 0 — the inputs. Take the commit from the preview deployment, not from the branch tip.
COMMIT=<sha>     # from the deployment — see the deployment TODO in §12.5
# Never build in the citizix checkout (§10). Full history, because build.sh passes
# --enableGitInfo and lastmod comes from git.
git clone --recurse-submodules https://github.com/etowett/citizix /tmp/preview-src
git -C /tmp/preview-src checkout "$COMMIT"
git -C /tmp/preview-src submodule update --init --recursive    # the pin, never --remote
hugo version        # 0.169.0 (citizix ci.yml:27; Cloudflare HUGO_VERSION)
sass --version

# 1 — the build Cloudflare ran, with the preview's build variables (§12.1).
(cd /tmp/preview-src && HUGO_PARAMS_RUNBOOK_SEO_ROBOTS="noindex, nofollow" ./build.sh)

# 2 — both gates, unmodified, against the rebuilt tree.
python3 scripts/check_links.py /tmp/preview-src/public
python3 scripts/check_budgets.py /tmp/preview-src/public --article-glob '*/index.html' \
        --baseline /tmp/stack-baseline.json --json /tmp/preview-budgets.json
```

Whether Cloudflare clones with full history matters here: a shallow clone would give every page
a different lastmod from this rebuild. One Cloudflare build log answers it — see the build-log TODO
in §12.5.

**Verified 2026-07-29, historical** — against a locally built citizix Docker image under the old
deploy: the extraction yielded 1,445 HTML files, and `check_links.py` ran over them in 3.5 s,
inferred `citizix.com` as the base host from the homepage canonical, found 530 distinct external
URLs and reported exactly one failure — `#security-hardening`, which is §9 defect 6 and is a
content bug in the archive. `check_budgets.py` ran over the same tree and reported the
distribution: p50 9,155, p90 11,630, max 47,503 B gz across 499 articles, homepage 6,725, worst
taxonomy list 5,159. That image was a **Stack** build, so those figures are §11's Stack column
reproduced independently, a few bytes apart because this was Apple gzip on macOS rather than the
Linux runner — the drift §11.1 warns about, visible. Nothing in either gate depends on how the
tree was produced, but the `build.sh` recipe above has not yet been run end to end — that is on
the pre-cutover list in §12.6.

Three reasons not to teach either script HTTP:

1. **A budget measured over the wire would be a worse number, not a more realistic one.** It
   would be the edge's compression at the edge's level, and
   [005 §5](../specs/005-performance-budgets.md) makes `gzip -n -9` part of the measurement
   precisely so two readings are comparable. A number produced a different way cannot be diffed
   against the baseline it exists to be diffed against.
2. **A crawler is a dependency surface.** Frontier, retries, rate limits, concurrency — in a
   repository whose thesis is the standard library and no toolchain
   ([ADR-1](../specs/006-architecture-decisions.md)).
3. **It would catch little the edge checks below do not.** What a crawl would newly see is the
   edge's behaviour — redirects, headers, status codes — and those are checked directly. What it
   would add over the rebuild, the served bytes themselves, is the one thing the recorded inputs
   above stand in for.

**The manual half is the edge, and it is short.** These are the facts that exist only in the
deployment and that no gate in this repository can reach. Run them against the preview host:

```bash
PREVIEW=https://<preview host>    # URL form: see the branch-builds TODO in §12.1

# a — the fixture set resolves to the status it should, and nothing is 5xx.
#     /tags/page/2/ and /categories/page/2/ must be 301: they are static/_redirects (§12.2),
#     not the theme.
for u in / /page/2/ /post/page/2/ /tags/ /categories/ /search/ /about-us/ \
         /sitemap.xml /index.xml /search/index.json; do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$PREVIEW$u")" "$u"
done
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$PREVIEW/tags/page/2/"        # 301 → /tags/
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$PREVIEW/categories/page/2/"  # 301 → /categories/

# b — noindex reaches the responses a <meta> tag cannot (§12.1, layer 3).
curl -sI "$PREVIEW/sitemap.xml" | grep -i x-robots-tag
curl -s  "$PREVIEW/robots.txt"          # production's file, by design — see §12.1 layer 2
```

There is no health endpoint any more: `/healthz` existed only for the Kubernetes probes and went
with them in citizix@`8918b75` (historical). Sweep (a) is the health check.

**What `check_budgets.py` sweeps as an article.** Since #64 it skips alias stubs and list pages
(§9 defects 4 and 8), so `/tags/` at +21.0% and `/search/` at three executable scripts no longer
report false failures, and its exit code means what it says on this tree. One caveat is still
true: regular pages outside `mainSections`, such as `/about-us/`, still count as articles, so read
any failure on one of those before treating it as a rollback trigger.

### 12.4 Rollback triggers

[010](../specs/010-citizix-migration.md) §5.6 names three. Two can be given a number today. The
third cannot, and saying so is the honest answer.

**Trigger 1 — any URL parity failure. The number is 1.**

`python3 scripts/check_parity.py` exits non-zero on a single difference that is not in
`.github/parity/reviewed-differences.json` with a reason. At `c98c01b` the reviewed set is 298
differences across 8 causes with **0 unreviewed** (§1) — 103 across 7 at `9ec479a` — so one
unreviewed difference is a regression by construction. Two of the eight are `defect: true`
rules (§1), which this trigger does not excuse: they are known and recorded, not new. On the deployed side the equivalent is the fixture-set sweep in
§12.3: any URL in §12.2 answering with a status other than the one that table predicts.

**Trigger 2 — any 5xx. The number is 1.**

A static tree served from Cloudflare's edge has no legitimate 5xx, so the first one is the
trigger. Nothing watches for it continuously any more: the Kubernetes liveness and readiness
probes on `/healthz` went with the cluster in citizix@`8918b75` (historical). So the fixture-set
sweep in §12.3 is the only check, which is why it is re-run during the observation period rather
than once. Whether the project reports responses by status code — the continuous half the
probes used to provide — (depends on the Pages/Workers TODO in §12).

**Trigger 3 — "any Lighthouse regression beyond threshold". This is not a trigger, and it cannot
be made into one from what exists.**

`TODO(eutychus): confirm what the citizix Lighthouse trigger should be.` It depends on two things
that do not exist yet, and inventing a number would be worse than leaving the gap visible:

- **There is no Lighthouse baseline, for citizix or for anything else.**
  `.github/lighthouse/lighthouserc.json` marks itself scaffold only and deliberately not wired
  into CI; [accessibility.md](accessibility.md) and [verification.md](verification.md) both record
  that no score exists. A regression needs something to regress from.
- **The numbers that do exist are for a different target.**
  [007 §3.3](../specs/007-verification.md) gates accessibility, best practices and SEO at 100 and
  performance at ≥ 98, median of 5 runs — **against the `exampleSite` demo, never against
  production citizix**, and [009 §3](../specs/009-showcase-compliance.md) gives the reason: citizix
  carries advertising and analytics. The same section requires citizix-like pages to be measured
  separately with third-party effects reported independently of first-party ones. So a citizix
  trigger needs a decision on whether GTM, GA4 and AdSense sit inside the threshold or outside it,
  and a pre-cutover run against production on this fixture set with pinned Chrome and Lighthouse
  versions to be the baseline. **[010](../specs/010-citizix-migration.md) §5.6 and
  [007 §3.3](../specs/007-verification.md) contradict each other on this point** and the spec is
  the place to settle it.

**What stands in until then, with numbers.** The theme's own byte budgets are measurable on the
§12.3 rebuild today and are most of what a performance regression would have been measuring:

| Rule | Number | Where it is written |
|---|--:|---|
| Per-page growth against the Stack baseline | **+2%** | `scripts/check_budgets.py`, `REGRESSION_TOLERANCE` |
| CSS, gzipped | **8,000 B** | `CSS_GZ_MAX` — Runbook measures 7,354 B, §11 |
| Core JS, gzipped | **3,000 B** | `CORE_JS_GZ_MAX` — measures 2,068 B |
| Search chunk, gzipped | **3,000 B** | `SEARCH_JS_GZ_MAX` |
| Executable `<script>` tags per article | **2** | `EXECUTABLE_SCRIPTS_MAX` |
| Third-party hosts the theme adds | **0** | `THIRD_PARTY_HOSTS_MAX` |

The per-page rule is the sharp one — a theme cannot compress content, but it must never render a
given page heavier than the theme it replaced did. Read it with §12.3's caveat that regular pages outside
`mainSections`, such as `/about-us/`, still count as articles.

### 12.5 The rollback command

**Confirm this before cutover, not after** — that is [010](../specs/010-citizix-migration.md)
§5.6's own instruction, and it is the step this section exists for.

**History, kept because the reasoning still applies.** §5.6 originally said *"the theme is a
submodule pin, so rollback is a submodule revert plus a redeploy"*, and on 2026-07-29 that was
false twice over: there was no Runbook submodule, and the old deploy workflow ran
`git submodule update --remote`, which builds each submodule's upstream tip rather than the
recorded pin, so reverting a pin changed nothing. The executable rollback was therefore a revert
of the deploy job's image-tag commit in a separate Argo CD releases repository (historical —
that repository is no longer in the path).

**Today, at citizix `6d22b64`:**

1. `.gitmodules` still has exactly one entry, `themes/hugo-theme-stack`. There is still no Runbook
   submodule; the cutover PR adds one, per [010](../specs/010-citizix-migration.md) §5 step 6.
2. `--remote` is gone. The deploy workflow it lived in was deleted in `8918b75`, and the same
   commit removed it from `ci.yml`; the commit message records that Cloudflare builds the pinned
   commit. So a pin now holds, and reverting it means something.
   `TODO(eutychus): confirm from one Cloudflare build log that submodules are checked out at the
   recorded commit, and whether the clone has full history (§12.3).`

So there are two rollbacks, and they are not alternatives — the first is fast, the second is what
makes the first stick.

**A — Cloudflare's rollback to the previous production deployment.** No rebuild: the previous
deployment's output already exists, so this re-points production at Stack bytes that were already
served. It also brings back the previous deployment's `_redirects`, without the two taxonomy
rules, which is correct for Stack (§12.2).
The rollback mechanism — dashboard path or CLI — and whether it takes effect immediately
(depends on the Pages/Workers TODO in §12). This section deliberately gives no command for it rather
than a guessed one.

**B — revert the cutover PR on `main`.** Every push to `main` deploys `main`, so after A the very
next merge — a content post, a Dependabot bump — redeploys Runbook. A is only a rollback until
then; B makes it permanent. Revert on a branch and merge it as a PR, like any other change to
citizix's `main`:

```bash
# BEFORE cutover — record the production deployment that is live, and its commit.
# These two strings are the rollback.
git -C ~/Code/my/citizix fetch origin
git -C ~/Code/my/citizix rev-parse origin/main       # the last Stack commit on main
# the live deployment's ID: see the deployment TODO below

# ROLLBACK, step B — after A, revert the cutover squash commit and let Cloudflare rebuild.
git -C ~/Code/my/citizix fetch origin
git -C ~/Code/my/citizix switch -c revert-runbook-cutover origin/main
git -C ~/Code/my/citizix revert --no-edit <cutover sha>    # one commit: squash-merged (§12.6)
# push the branch, open a PR, merge it — that merge is the deploy.
```

`TODO(eutychus): confirm the deployment ↔ commit ↔ live mapping on Cloudflare — where a
deployment's commit and ID are shown, and how to tell that the production deployment for a given
commit is live.` §12.3 step 0, the record above and the post-cutover checks in §12.6 all need it.

B is a rebuild, so it is minutes, not seconds, and it reverts everything in the cutover PR.
**Keep that PR to the theme switch and the two `_redirects` lines and nothing else**, so that
reverting it cannot take a content change with it, and so that no unrelated change is stacked on
top before the observation period ends.

**Neither has been run.** [010](../specs/010-citizix-migration.md) §5.6 requires confirming the
rollback before cutover, and confirming means executing it and watching the site return to Stack,
not reading it and agreeing that it looks right. B can be rehearsed end to end on a preview
branch. A acts on production by definition, so it needs a rehearsal that is safe there — rolling
back to the deployment before the live one and forward again, at a quiet moment, is the obvious
candidate, and the one 010 §5 step 6 asks for. A rollback that has been run once is a rollback; one that has only been written down is a plan.

### 12.6 Cutover, and the observation period

**Cutover is merging the cutover PR into citizix's `main`.** Cloudflare builds and deploys every
push to `main`, so there is no separate deploy step — the merge is the deploy — and the
deliberateness that [010](../specs/010-citizix-migration.md) §5.5's manual `workflow_dispatch`
used to supply (historical) now has to come from the person merging. **Squash-merge it** — [010](../specs/010-citizix-migration.md) §5 step 5 requires it, so the
cutover is one commit and §12.5's revert is one command. Merge it on purpose, at a time chosen for
it, with nothing else queued to merge behind it.

Before merging:

1. Run the §12.3 `build.sh` rebuild once end to end at the current citizix head, and record the
   commit, Hugo and Sass versions with the results.
2. Rehearse A and B from §12.5.
3. Record the live production deployment and `origin/main` (§12.5).

Once the Cloudflare build for the merge commit is live (§12.5's deployment TODO), run the §12.3
edge checks against production rather than the preview, and re-run the §12.2 fixture set. Then
verify Disqus (§12.7).

**The observation period.** [010](../specs/010-citizix-migration.md) §5.7 says "a defined period"
and §6 places it between cutover and showcase submission, but no file defines it. A floor is
derivable from what is actually scheduled, which is a better basis than a round number:

| Job | Cadence |
|---|---|
| Demo build and gates against latest Hugo (`scheduled.yml`) | nightly, 22:00 UTC |
| External link sweep (`scheduled.yml`) | weekly, Mondays 03:00 UTC |
| Archive parity (`parity.yml`) | weekly, Sundays 04:00 UTC |

The longest cadence is weekly, so **7 days is the shortest period that contains one full pass of
every scheduled gate**, and it has to span both a Sunday and a Monday to get one of each.
**Proposed: 14 days** — two full passes, so that a failure has a chance to reproduce instead of
being read as a flake, which on a weekly job is otherwise a fortnight's wait anyway.
`TODO(eutychus): confirm — 7 is derived, 14 is a proposal, and`
[010](../specs/010-citizix-migration.md) `§5.7 is the file that should record whichever it is.`

### 12.7 Disqus thread continuity — what is verified and what is not

§6 says every existing thread reattaches by itself because threads key on the page URL and post
URLs are unchanged. The first half of that is now verified precisely; the second half is not, and
this is the `TODO(eutychus): confirm` from #47.

**Verified.** Runbook's
[`layouts/_partials/hooks/comments.html`](../layouts/_partials/hooks/comments.html)
is an intentionally empty extension point — it does nothing beyond existing, by design
([ADR-8](../specs/006-architecture-decisions.md)), so the theme contributes no behaviour here at
all. On the Stack side, `layouts/_partials/comments/provider/disqus.html` wraps a call to Hugo's
internal `disqus.html`, and that template sets `this.page.identifier` **only** when
`.Params.disqus_identifier` is present. No page, config key or layout anywhere in citizix sets
`disqus_identifier`, `disqus_url` or `disqus_title`. So today's threads are keyed on the URL, and
the URLs do not change (§1).

**Not verified, and the reason it matters.** The Disqus snippet in
[extending.md](extending.md#disqus) sets `this.page.identifier = {{ .Permalink }}` **explicitly**,
which is a change from what citizix sends today, namely nothing. Whether Disqus matches an
existing URL-keyed thread the first time an identifier is supplied for it is Disqus's behaviour,
not Hugo's, and it cannot be established from any file in either repository. Nothing has ever been
exercised against a real citizix thread ID.

So make it a numbered cutover step rather than an assumption. Immediately after cutover, open a
post known to carry comments and confirm the existing thread renders with its existing comment
count, before anything else is declared fine. If it does not, the fix is to drop the explicit
`this.page.identifier` line and let Disqus fall back to the URL as it does today.
`TODO(eutychus): confirm which post to use — it needs the highest comment count in the Disqus
admin for shortname citizix, which is not visible from either repository.`

### 12.8 The §3 override loose end, closed

[010](../specs/010-citizix-migration.md) §3 left `layouts/sitemap.xml` as
*"Evaluate: is the image-extension and priority logic a Runbook capability or citizix-only?"*.
**Disposition: citizix-only, and delete rather than port.** §5 above carries the full reasoning
and the measurement; in short, Runbook ships no sitemap template at all, Hugo's internal one is
what the site should serve, and the parity manifest confirms the `<loc>` set is unchanged. The only
sitemap difference the run reports is two `<image:loc>` entries, recorded in
`.github/parity/reviewed-differences.json` with the reason. That closes the last of §3's ten
files.
