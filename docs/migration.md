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

**Post URLs are theme-independent.** 499 of 500 posts pin their own `url:` in front
matter, and a theme cannot change front matter. The configured `permalinks.post` is
never consulted. So the check most people would run — "do the article URLs match?" —
passes trivially and proves nothing.

**351 of 354 aliases are Hugo's own.** They are the automatic `/page/1/` paginator
aliases that any theme regenerates, plus 22 term-merge redirects that live in taxonomy
`_index.md` front matter and are equally theme-independent.

What the theme genuinely controls, and what the manifest diff found:

| Surface | Result |
|---|---|
| Post, page, section, term URLs | **identical** |
| Home and section pagination `/post/page/{n}/` | **identical** |
| `/search/` | **still exists**, HTML + RSS + JSON |
| RSS feed paths (331 feeds) | **identical** |
| Canonical, `og:url` | **identical on every page that still exists** |
| `/tags/page/{n}/`, `/categories/page/{n}/` | **31 URLs removed** — §4 |
| JSON-LD `mainEntityOfPage` | **removed from 4 non-article pages** — deliberate, §4 |
| RSS item lists | **2 feeds differ** — both by design, §9 |
| Sitemap `<loc>` | identical; 2 `<image:loc>` entries dropped — §5 |

Totals: **103 differences across 7 causes, 0 unreviewed.** The reasoning for each is
recorded in `.github/parity/reviewed-differences.json`, where the reason field is
structurally mandatory.

Measured at citizix@`9ec479a`, Hugo v0.164.0+extended. The file records the ref it was
derived at, because a reviewed difference is only true of the content commit it was
reviewed against.

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
documents, 178,113 B, in Runbook's own `{"v":1,"docs":[…]}` schema, against the 4,617,791 B
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
Neither spelling appears anywhere in the corpus at `9ec479a`. Kept as a note because both
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

- server-side, in `nginx.conf` — one `location ~ ^/tags/page/` block; or
- `aliases:` on `content/tags/_index.md` and `content/categories/_index.md`, which makes
  Hugo emit the meta-refresh stubs. Cheaper to review, worse for crawlers than a 301.

Prefer the server rule. citizix already serves through nginx — and has done this since
citizix#86, which is in the pinned ref: `nginx.conf` carries
`location ~ ^/tags/page/[0-9]+/?$` and its `/categories/` twin, both `return 301`. This
step is **done** for the reference archive and is recorded here for anyone migrating
another one.

**Cost of the change, measured** at `9ec479a`: `/tags/` grows from 4,544 to 5,496 B
gzipped (+21.0%) because it now carries all 297 terms on one page. It replaces 30 HTTP
round-trips with one. Two caveats on that number — it is above the 6,000 B list-page
budget's older 5,205 B reading because the corpus gained terms, and the per-page
no-regression rule in `check_budgets.py` fails on it, since that rule is scoped by
`--article-glob` and `/tags/` is not an article. See §9 defect 8.

### `/search/` and everything else

`/search/` still exists at the same path, still carries its menu entry, and still emits
HTML and RSS — plus JSON, which is Runbook's search index and is why §3 says to keep
`outputs: json` rather than drop it. Section pagination (`/post/page/{n}/`), home
pagination, all 331 RSS feed paths, the sitemap URL set and every canonical are
unchanged.

---

## 5. The override files, classified

citizix carries **eleven** local layout overrides — [010](../specs/010-citizix-migration.md)
§3 lists ten and omits `layouts/_partials/head/head.html`.

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
| `layouts/sitemap.xml` | **citizix-only** | Delete. Reasoning below |

Six of eleven collapse into ADR-8 hooks that already exist in
`layouts/_partials/hooks/`; three are Runbook capabilities outright; two are deleted.
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

**Runbook should not ship a sitemap override.** Hugo's internal sitemap (`<loc>` +
`<lastmod>`) is what this site should serve, and the manifest diff confirms the URL set
is byte-for-byte the same.

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

This build has **zero** zero-post term pages, in both themes — verified through the
`numberOfItems` field Runbook writes into each term page's `CollectionPage` JSON-LD,
which is also the cheapest way to check it on your own site.

---

## 9. Defects this migration found

Reported rather than fixed, because these files belong to other workstreams
(contracts §0) and a cross-boundary edit is a merge conflict. The one exception is
defect 3: a single line in `scripts/check_links.py`, which no round-2 workstream owns,
and which was failing the nightly job on `exampleSite` — that one is fixed here and
called out as such. Each defect below is reproducible with the commands in §10.

| # | Where | What |
|---|---|---|
| 1 | `layouts/rss.xml` | **FIXED in #25.** The home feed used `site.RegularPages` instead of filtering to `params.mainSections`, so `/about-us/`, `/contact-us/`, `/privacy-policy/` and `/search/` were published as feed items. At `9ec479a` both themes' `/index.xml` carry the same 491 items and the reviewed-difference rule that allowed it has been deleted |
| 2 | `layouts/rss.xml` | **FIXED in #25.** Ranged `.RegularPages`, which is **empty** on a taxonomy list kind, so `/tags/index.xml` and `/categories/index.xml` shipped as valid but empty channels. They now collect the pages carrying any term in the taxonomy. The two feeds still *differ* from Stack's, which list term pages rather than articles — that is a design difference and is recorded as one, no longer as a defect |
| 3 | `scripts/check_links.py` | **FIXED IN THIS CHANGE** (one line, in a file no running workstream owns). A heading id containing a non-ASCII character is emitted raw in `id=` and percent-encoded in `href=` — `id=step-3-—-optional-…` against `href=#step-3-%e2%80%94-optional-…`. That is not a theme bug: Go's `html/template` normalises URL-context attributes and `safeURL` does not suppress it, and a user agent percent-decodes a fragment before matching ids, so both spellings address the same element. The checker was comparing them raw. See below — this was **already failing on `exampleSite`**, not only on the archive |
| 4 | `scripts/check_budgets.py` | `--article-glob` defaults to `posts/*/index.html`, which matches nothing on a site using flat `/:slug/` permalinks; the script then silently falls back to "the first page that matches", which on this archive is an **alias stub**, and reports the theme-shell CSS and JS as "not built yet". The fallback should skip meta-refresh pages |
| 5 | `exampleSite/content/posts/image-and-figure.md` | References `/not-fetched.png`, which is not in the build. The only remaining `check_links.py` failure on `exampleSite` after defect 3 was fixed. Either the asset is missing or the fixture is deliberately testing a broken image, in which case it needs a recorded exclusion |
| 6 | citizix content | **FIXED UPSTREAM in citizix 49fdb91**, which is inside the `9ec479a` pin. `/production-grade-saltstack-multi-environment-gitops-almalinux-10/` linked to `#security-hardening`, which no heading on that page defined; it was pre-existing and failed on the Stack build too, so it was the archive's to fix rather than the theme's. At this pin the page carries neither the dangling `href` nor the `id`, and the first execution of the parity job (run 30436578455) reports no broken internal links, subresources or fragments across the whole build. `parity.yml` runs the link crawl **blocking** again as a result |
| 7 | `docs/verification.md` §2, §8 | Both say the internal link and fragment crawl "runs per PR". It does not — `ci.yml` runs only the REQ-CB-1, fixture, JSON-LD and budget gates. `check_links.py` runs in `scheduled.yml`, nightly |
| 8 | `scripts/check_budgets.py` | The per-page script-tag and no-regression rules are scoped by `--article-glob`, which on a flat `/:slug/` archive is `*/index.html` and therefore matches pages that are not articles. Two consequences at `9ec479a`, both of them intended behaviour reported as failures: `tags/index.html` trips the 2% no-regression rule at +21.0% (§4, and already a reviewed `url` difference), and `search/index.html` trips the 2-executable-script budget at 3 — the inline theme guard, `runbook.js`, and the lazily-loaded search chunk that the same script *also* budgets separately as `SEARCH_JS_GZ_MAX`. Counting that chunk twice means the gate contradicts itself on the one page that loads it. Same root cause as defect 4. Until it can tell an article from a browse page, `parity.yml` runs the budget step `continue-on-error` |

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
        --expect-pages 1064 --expect-aliases 356

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

**The theme-shell rows were re-measured at `9ec479a`; the distribution table below it was
not.** Runbook's shell has grown since this section was written — CSS by 82% as the
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
is 178,113 B raw against Stack's 4,617,791 B — 26× smaller on the same 491 posts — and
that is a schema decision rather than a compression win. Stack stores the full `content`
of every article; Runbook stores five short keys per document (`t` title, `u` permalink,
`d` date, `s` a summary truncated at `summaryLength`, `g` taxonomy terms), which is what
`layouts/search.json` emits.

Page-weight distribution across the 489 pages that are articles in both builds,
**still as measured at `dc1b321`** — re-deriving it at the new pin mixes corpus drift
into a theme comparison, and the first real CI run is the place to do that properly.
`TODO(eutychus): re-derive §11's distribution table from a parity run at 9ec479a once
CITIZIX_TOKEN is set.`

| | Stack | Runbook | |
|---|--:|--:|--:|
| p50 | 9,150 B gz | **6,795 B** | −25.7% |
| p90 | 11,603 B gz | **9,302 B** | −19.8% |
| max | 47,315 B gz | 47,453 B | +0.3% |
| homepage | 6,753 B gz | **4,106 B** | −39.2% |
| worst term page | 5,174 B gz | **3,570 B** | −31.0% |
| archive total | 4.56 MiB | **3.46 MiB** | −24.1% |
| articles under 7 KB gz | 39 (7.9%) | **254 (51.9%)** | |

**Exactly one article of 489 gets heavier**, by 138 B (+0.3%) — and it is the largest
page in the archive, where Runbook's per-block chrome on 158 code blocks costs more than
it saves. It is inside `check_budgets.py`'s 2% no-regression tolerance.

### 11.1 Proposed page-weight thresholds

[005 §3.1](../specs/005-performance-budgets.md) requires these to be re-derived before
M3 because the numbers in §3.2 were set against a Stack median of 10,663 B that the
reference site has since improved to 9,150 B without Runbook existing.

> ### ⚠️ Platform
>
> **These numbers are GNU gzip 1.13 on Linux (x86-64 container), which is what
> `ubuntu-latest` runs.** They are not the macOS numbers.
> [verification.md §1](verification.md#reproducibility) records that GNU gzip and Apple
> gzip disagree, and a baseline captured on a laptop and compared on a runner reports a
> regression that is really a difference of gzip implementation.
>
> The same build measured with **Apple gzip 479** on macOS reads p50 6,768 and p90
> 9,296 against Stack's 9,159 / 11,616 — a drift of up to 30 B, small on files this
> size but real. Do not mix them.

`scripts/check_budgets.py` is owned by the fixtures/CI workstream, so these are proposed
here for someone else to apply. Replace `PLACEHOLDER_PAGE_WEIGHT` with:

```python
PLACEHOLDER_PAGE_WEIGHT = {
    "article_p50": 7_200,   # measured 6,764 — Stack 9,130
    "article_p90": 9_800,   # measured 9,296 — Stack 11,614
    "homepage":    4_400,   # measured 4,106 — Stack 6,753
    "list_page":   3_800,   # measured 3,570 — Stack 5,174 (worst term page)
}
```

Measured values are `check_budgets.py`'s own output on the Runbook archive build with
`--article-glob '*/index.html'`, which is the glob a flat-permalink site needs (defect
#4 in §9). Each threshold carries **5–7% headroom** over the measured value, because a
pinned corpus is re-pinned occasionally and a gate that fails the day a post is added
teaches people to raise the number rather than investigate it.

Three conditions on using them:

1. **Enforce them in `.github/workflows/parity.yml` only, never in `ci.yml`.** These are
   archive numbers. `exampleSite`'s article p50 is around 2,600 B, so enforcing them
   there passes trivially and measures nothing — the exact failure mode
   [005 §3.1](../specs/005-performance-budgets.md) warns about.
2. **The no-regression rule is the sharp instrument.** The distribution gate catches a
   theme-wide regression; the per-page baseline catches the one page in 489 that got
   worse. Keep both, and regenerate the baseline whenever the pinned content moves.
3. **Re-derive on the runner before turning `--enforce-page-weight` on.** These numbers
   came from a container on an arm64 laptop, not from a GitHub runner. The gzip
   implementation matches; nothing else was verified.

---

## 12. Cutover

[010](../specs/010-citizix-migration.md) §5 defines six steps. Steps 1 and 2 are done and are
§1 above. Steps 3 to 6 had no executable form at all, which is what this section is: the
preview recipe, the pages to compare by eye, the rollback triggers as numbers, and the
rollback command.

It is worth being blunt about why it is written down rather than improvised. Every other gate
in this repository exists because someone decided a green tick should mean something. The
cutover has no tick. It is a human procedure — [010](../specs/010-citizix-migration.md) §5.5
records that citizix deploys by manual `workflow_dispatch` only, and that this is deliberate
and must not be automated — so an unwritten procedure is the risk here, not the theme. And the
one step that has to work first time, on the day it is needed, under pressure, is the rollback,
which is also the only one that has never been run (§12.6).

Everything below is measured at citizix@`9ec479a`, the ref `.github/workflows/parity.yml` pins,
unless it says otherwise.

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

**Measured on `exampleSite`, Hugo v0.164.0:** 34 of the build's 46 HTML files gain
`<meta name=robots content="noindex, nofollow">`. The 12 that do not are Hugo's own
meta-refresh alias stubs — the build reports `Aliases 12` — and each contains nothing but a
`<link rel=canonical>` and a `<meta http-equiv=refresh>`. **Hugo's internal alias template emits
no robots directive**, so this layer does not cover an alias stub, and it cannot cover
`/index.xml`, `/sitemap.xml` or `/search/index.json` at all, because none of those can carry a
`<meta>` tag. On the archive that is 356 alias stubs plus 331 feeds outside the directive.

**Layer 2 — `robots.txt`, which citizix already owns.** `static/robots.txt` is copied verbatim
into the build, so nothing a theme does can override it, and Hugo generates none of its own here
(`enableRobotsTXT` is not set in `config.yaml`). The production file ends `Allow: /` and
`Sitemap: https://citizix.com/sitemap.xml`. Deployed unchanged to a preview host, it invites
crawling and advertises production's sitemap. **The preview must serve its own** — `User-agent: *`
/ `Disallow: /` — and this is a citizix-side change, not a theme one.

**Layer 3 — an `X-Robots-Tag` response header at the edge.** This is the only layer that reaches
every response: the alias stubs, the feeds, the sitemap and the search index included. It belongs
in the preview's `nginx.conf` server block alongside the 301s already there, and it is also
citizix-side. Layer 1 is still worth having even with layer 3 in place, because it survives being
served from somewhere other than that nginx.

**What the preview must not change: `baseURL`.** `Dockerfile:4` hardcodes `-b https://citizix.com`,
so a preview built from the unmodified Dockerfile emits production canonicals. Leave it. A
canonical pointing at production is the correct duplicate-content signal for a temporary copy,
and the canonical *values* are already asserted by `check_parity.py` in the parity job, so nothing
is lost by not re-deriving them against a preview host. Pointing it at the preview would buy
nothing and would make §1's canonical row unverifiable on the artefact you are about to ship.

**Disqus must be off on the preview.** §6's snippet lives in the *site*, and citizix's Disqus
shortname is a live account. Rendering the embed on a preview host registers new, empty threads
keyed on preview URLs, in the same account that holds years of real ones. Leave
`disqusShortname` unset in the preview config; an empty comment area on the preview is expected
and is not evidence of anything. Thread continuity is verified on production after cutover —
§12.7.

### 12.2 The fixture set to compare page-by-page

[010](../specs/010-citizix-migration.md) §5.3 says "the pinned fixture set" without saying which
pages. Reviewing 1,064 pages by eye is not a procedure, and reviewing a random 20 proves nothing.
These are the 21 URLs where something in this document says the theme changes behaviour, so each
one is in the list because a named section predicts what it should look like. Open each on the
preview and on production side by side.

| URL | What it is here to catch |
|---|---|
| `/` | Home. Carries `image: /og-default.png` (`content/_index.md`), so it is one of the two pages the retired sitemap image extension fired on — §5 |
| `/page/2/` | Home pagination survives — §4 |
| `/post/page/2/` | Section pagination survives — §4 |
| `/how-to-install-and-configure-redis-6-on-ubuntu-20-04/` | The representative article §11's theme-shell figures are read from |
| `/kubernetes-tls-security-hardening-guide-traefik-nginx/` | The largest page in the archive at 47,503 B gz, and the **one article of 489 that gets heavier** under Runbook (+138 B, +0.3%) — §11 |
| `/how-to-install-and-configure-puppet-7-server-on-ubuntu-20-04/` | [010](../specs/010-citizix-migration.md) §1 bug 1 — everything after the unterminated fence used to render inside a single code block |
| `/how-to-install-and-configure-postgres-13-on-centos-8/` | §1 bug 2 — the last bare `<pre><code>` in the entire build |
| `/production-grade-saltstack-multi-environment-gitops-almalinux-10/` | §9 defect 6. It must still fail **identically** on both themes, not differently |
| `/how-to-secure-kubernetes-clusters-with-firewalld-and-saltstack-almalinux-10-production-ready/` | The only post using the `admonition` shortcode — §5's replacement, and the page that proves the admonition CSS moved out of the per-page `<style>` |
| `/install-manjaro-21-gnome-step-by-step-with-screenshots/` | `image: /android-chrome-512x512.png` — the second image-sitemap page, and the OG-image path — §5 |
| `/tags/` | §4 — unpaginated, all 297 terms, 4,544 → 5,496 B gz |
| `/categories/` | §4 — same change, 28 terms |
| `/tags/page/2/` | Must **301 to `/tags/`**. That redirect is `nginx.conf`, not the theme, so the manifest diff cannot see it |
| `/tags/amazon-eks/` | REQ-TAX-1 — a term whose title comes from `params.runbook.taxonomyTitles` rather than from an `_index.md` |
| `/tags/k8s---docker/` | REQ-TAX-2 — a retired term whose redirect lives as `aliases:` on the surviving `/tags/k8s/`. Deleting the wrong file breaks this silently — §8.2 |
| `/search/` | §3 — the page, the UI, and the widget's dependence on `outputs: json` |
| `/search/index.json` | §3 — 491 documents. `check_parity.py` walks `.html` and `.xml` only, so nothing in the manifest diff would notice it missing |
| `/about-us/` | §5 — one of the four pages that lose `mainEntityOfPage` and gain `@type WebPage`. It also carries the archive's only three front-matter `aliases:` — §1 |
| `/privacy-policy/` | Same, plus the `latmod:` typo fix that landed upstream — §3 |
| `/index.xml` | §9 defects 1 and 2 — the home feed, 491 items, no `/about-us/` |
| `/sitemap.xml` | §5 — the override is deleted, and Hugo's internal sitemap must produce the same `<loc>` set |

`/contact-us/` is deliberately absent: it changes in exactly the same way as `/about-us/` and
`/privacy-policy/`, and a fixture set nobody finishes is worse than a shorter one.

### 12.3 Checking the preview — what is automated and what is not

[010](../specs/010-citizix-migration.md) §5.4 asks for the link crawl and the budget gates
against the preview. **Neither `scripts/check_links.py` nor `scripts/check_budgets.py` was taught
to speak HTTP, and that is a decision rather than an omission.** Both want a *tree*, and the
preview already serves one, so the tree is what they get — extracted from the image that is
actually deployed, which is stronger evidence than rebuilding locally and assuming the image
matches.

```bash
# 1 — pull the deployed artefact out of the image that is running.
#     Dockerfile:8 — COPY --from=build /site/public /usr/share/nginx/html
CID=$(docker create ektowett/citizix:"$PREVIEW_TAG")
docker cp "$CID":/usr/share/nginx/html /tmp/preview-tree
docker rm "$CID"

# 2 — both gates, unmodified, against the bytes the preview is serving.
python3 scripts/check_links.py /tmp/preview-tree
python3 scripts/check_budgets.py /tmp/preview-tree --article-glob '*/index.html' \
        --baseline /tmp/stack-baseline.json --json /tmp/preview-budgets.json
```

**Verified 2026-07-29** against a locally built citizix image: the extraction yields 1,445 HTML
files, and `check_links.py` runs over them in 3.5 s, infers `citizix.com` as the base host from
the homepage canonical, finds 530 distinct external URLs and reports exactly one failure —
`#security-hardening`, which is §9 defect 6 and is a content bug in the archive. `check_budgets.py`
runs over the same tree and reports the distribution: p50 9,155, p90 11,630, max 47,503 B gz
across 499 articles, homepage 6,725, worst taxonomy list 5,159. That image is a **Stack** build,
so those figures are §11's Stack column reproduced independently, a few bytes apart because this
was Apple gzip on macOS rather than the Linux runner — the drift §11.1 warns about, visible.

Three reasons not to teach either script HTTP:

1. **A budget measured over the wire would be a worse number, not a more realistic one.** It
   would be nginx's gzip at nginx's level, and [005 §5](../specs/005-performance-budgets.md)
   makes `gzip -n -9` part of the measurement precisely so two readings are comparable. A number
   produced a different way cannot be diffed against the baseline it exists to be diffed against.
2. **A crawler is a dependency surface.** Frontier, retries, rate limits, concurrency — in a
   repository whose thesis is the standard library and no toolchain
   ([ADR-1](../specs/006-architecture-decisions.md)).
3. **It would catch nothing new.** The bytes served are the bytes extracted. Everything an HTTP
   crawl would newly see is an nginx concern, and those are below.

**The manual half is the edge, and it is short.** These are the facts that exist only in the
deployment and that no gate in this repository can reach. Run them against the preview host:

```bash
PREVIEW=https://<preview host>

# a — the fixture set resolves to the status it should, and nothing is 5xx.
#     /tags/page/2/ is the one that must be 301: it is nginx.conf, not the theme.
for u in / /page/2/ /post/page/2/ /tags/ /categories/ /search/ /about-us/ \
         /sitemap.xml /index.xml /search/index.json; do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "$PREVIEW$u")" "$u"
done
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$PREVIEW/tags/page/2/"   # 301 → /tags/

# b — noindex reaches the responses a <meta> tag cannot (§12.1).
curl -sI "$PREVIEW/sitemap.xml" | grep -i x-robots-tag
curl -s  "$PREVIEW/robots.txt"          # must be the preview's Disallow: /, not production's

# c — health. helm/prod.yml probes this every 30 s, so it is already being watched.
curl -s "$PREVIEW/healthz"              # {"status":"ok"}
```

**What `check_budgets.py` still needs**, named here rather than changed because stream D owns it
(contracts §1): the two `--article-glob` defects in §9 (4 and 8). Until the script can tell an
article from a browse page or an alias stub, its exit code is not usable as a cutover trigger and
you have to read the individual failures — `/tags/` at +21.0% and `/search/` at three executable
scripts are both expected, both already reviewed, and neither is a rollback trigger.

### 12.4 Rollback triggers

[010](../specs/010-citizix-migration.md) §5.6 names three. Two can be given a number today. The
third cannot, and saying so is the honest answer.

**Trigger 1 — any URL parity failure. The number is 1.**

`python3 scripts/check_parity.py` exits non-zero on a single difference that is not in
`.github/parity/reviewed-differences.json` with a reason. At `9ec479a` the reviewed set is 103
differences across 7 causes with **0 unreviewed** (§1), so one unreviewed difference is a
regression by construction. On the deployed side the equivalent is the fixture-set sweep in
§12.3: any URL in §12.2 answering with a status other than the one that table predicts.

**Trigger 2 — any 5xx. The number is 1.**

A static nginx serving a static tree has no legitimate 5xx, so the first one is the trigger.
Kubernetes is already watching half of this continuously: `helm/prod.yml` sets liveness and
readiness probes on `/healthz` at `periodSeconds: 30`, so a pod that stops serving is failed out
without anyone looking. What the probe does not catch is a 5xx on a *page* while `/healthz` still
returns 200, which is why the fixture-set sweep is run rather than just trusting the probe.

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
preview artefact today and are most of what a performance regression would have been measuring:

| Rule | Number | Where it is written |
|---|--:|---|
| Per-page growth against the Stack baseline | **+2%** | `scripts/check_budgets.py`, `REGRESSION_TOLERANCE` |
| CSS, gzipped | **8,000 B** | `CSS_GZ_MAX` — Runbook measures 7,354 B, §11 |
| Core JS, gzipped | **3,000 B** | `CORE_JS_GZ_MAX` — measures 2,068 B |
| Search chunk, gzipped | **3,000 B** | `SEARCH_JS_GZ_MAX` |
| Executable `<script>` tags per article | **2** | `EXECUTABLE_SCRIPTS_MAX` |
| Third-party hosts the theme adds | **0** | `THIRD_PARTY_HOSTS_MAX` |

The per-page rule is the sharp one — a theme cannot compress content, but it must never render a
given page heavier than the theme it replaced did. Read it with §12.3's caveat about the two known
false failures.

### 12.5 The rollback command

**Confirm this before cutover, not after** — that is [010](../specs/010-citizix-migration.md)
§5.6's own instruction, and it is the step this section exists for.

§5.6 says: *"the theme is a submodule pin, so rollback is a submodule revert plus a redeploy."*
**That is not true of citizix today, in two independent ways, both verified 2026-07-29:**

1. `.gitmodules` has exactly one entry, `themes/hugo-theme-stack`. There is no Runbook submodule
   to revert.
2. `.github/workflows/deploy-k8s.yml:26` runs `git submodule update --init --recursive --remote`.
   `--remote` updates each submodule to the tip of its **remote default branch** instead of the
   commit the superproject records, so the recorded pin is not what gets built. Adding Runbook as
   a submodule without removing that flag would produce a pin that reverting does not change.

`--remote` has a consequence today that has nothing to do with Runbook: **the deployed Stack
version is whatever upstream `main` holds at deploy time, not what the repository records.**

So the rollback that can actually be executed is not a submodule revert. It is at the deployment
layer, and it is better than a submodule revert anyway, because it involves no rebuild. The deploy
job writes a new image tag into the `argocd-releases` repository (`deploy-k8s.yml:84-93`): it
copies the rendered manifests into `apps/citizix/prod/<tag>/`, `sed`s the tag in
`argocd-apps/prod-citizix.yml`, commits as `updated prod citizix with new image tag <tag>` and
pushes. Argo CD reconciles from there.

```bash
# BEFORE cutover — record the tag that is live. This string is the rollback.
grep '^  tag:' ~/Code/my/citizix/helm/prod.yml       # main-374610d at the time of writing

# ROLLBACK — revert the single commit the deploy job made in argocd-releases.
git -C argocd-releases log --oneline -1              # "updated prod citizix with new image tag <new>"
git -C argocd-releases revert --no-edit HEAD
git -C argocd-releases push origin main
```

The previous image is immutable and already in the registry, so this re-points Argo at manifests
that already exist rather than rebuilding anything.

`TODO(eutychus): confirm the Argo CD sync policy for prod-citizix — whether it auto-syncs or needs
a manual sync, and the reconciliation window.` That is the difference between a rollback measured
in seconds and one that needs a second manual step, and it is not recorded in any file in either
repository.

**This command has never been run.** [010](../specs/010-citizix-migration.md) §5.6 requires
confirming it before cutover; confirming means executing it against the preview and watching the
preview return to Stack, not reading it and agreeing that it looks right. A rollback that has been
run once is a rollback; one that has only been written down is a plan.

### 12.6 Cutover, and the observation period

Cut over by dispatching `deploy-k8s.yml` by hand.
[010](../specs/010-citizix-migration.md) §5.5 records that citizix deploys by manual
`workflow_dispatch` only and that this must not be automated; nothing here changes that.

Immediately after the deploy reconciles, run the §12.3 edge checks against production rather than
the preview, and re-run the §12.2 fixture set. Then verify Disqus (§12.7).

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
