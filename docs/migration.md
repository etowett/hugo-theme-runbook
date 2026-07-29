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
| 6 | citizix content | `/production-grade-saltstack-multi-environment-gitops-almalinux-10/` links to `#security-hardening`, which no heading on that page defines. **Pre-existing** — it fails on the Stack build too. A citizix fix, not a theme one |
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
