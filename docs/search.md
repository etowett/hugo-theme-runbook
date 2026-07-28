# Search

Client-side search over a **metadata-only** index. Requirements are
[003 §3.4](../specs/003-design-spec.md); the budget is
[005 §3.1 and §4](../specs/005-performance-budgets.md); the shape of the JavaScript is
[ADR-5](../specs/006-architecture-decisions.md).

Ten files implement it and nothing else touches it:

| File | Does |
|---|---|
| `layouts/search.html` | The `/search/` page |
| `layouts/search.json` | The index, emitted at `/search/index.json` |
| `layouts/_partials/search/settings.html` | Reads `params.runbook.search.*` |
| `layouts/_partials/search/ui.html` · `browse.html` · `js.html` | Form, browse alternative, script tag |
| `assets/js/search/index.js` · `engine.js` | The lazy chunk — UI and ranking |
| `assets/css/search.css` | Every visual rule, including the zero-JS state |

---

## Turning it on

Three things, and the second one is the one people forget.

**1. Enable the feature.**

```toml
[params.runbook.search]
  enable = true
```

It is `false` by default. A theme that ships a search page nobody asked for has added a URL to
every consumer's site.

**2. Create the page, with a JSON output format.**

```yaml
# content/search.md
---
title: "Search"
layout: "search"
outputs:
  - html
  - json
---

Optional prose here — it renders under the results.
```

`layout: "search"` selects `layouts/search.html`, the same way `layout: "archive"` selects the
archive template. **`outputs` is what emits the index**: without it there is a search page and
nothing to search. The page renders its browse list and an HTML comment saying exactly that,
rather than failing the build — a build warning would trip `--panicOnWarning` for a site that
is merely half-configured.

**3. Nothing else.** The header link, the JSON-LD `SearchAction` and the lazy chunk all follow
from step 1.

### `/search/` is a fixed path

[010 §2](../specs/010-citizix-migration.md) lists `/search/` among the URLs the reference-site
migration must not move, and the parity diff fails if it does. The index lands beside it at
`/search/index.json` — the same URL the reference site serves today, so the migration is a
no-op for anything already pointing at it. What changes is the payload.

---

## Indexed fields

This closes **open decision #5** in
[006](../specs/006-architecture-decisions.md#decisions-still-open). Measurements are in
[the next section](#the-budget-and-what-was-rejected).

```json
{
  "v": 1,
  "docs": [
    {
      "t": "How to install and configure Redis 7 on Rocky Linux 9",
      "u": "/how-to-install-and-configure-redis-7-on-rocky-linux-9/",
      "d": "2024-03-01",
      "s": "Install Redis 7 on Rocky Linux 9, set a password, bind it to a private…",
      "g": ["Redis", "Rocky Linux", "Databases"]
    }
  ]
}
```

| Key | Field | Source |
|---|---|---|
| `v` | index format version | Literal `1`. The chunk refuses an index it does not understand, so a stale cached one from an older theme cannot render garbage |
| `t` | title | `.LinkTitle` |
| `u` | URL | `.RelPermalink` |
| `d` | date | `.Date`, `YYYY-MM-DD`. Absent on an undated page |
| `s` | summary | `.Description`, else the page content with code stripped. Capped — see `summaryLength` |
| `g` | terms | Display titles from every taxonomy in `taxonomies`, flattened and de-duplicated |

**The keys are one character on purpose.** Long ones (`"title"`, `"summary"`, …) cost about
20 KB raw across the reference archive — 8% of the budget — and almost nothing gzipped, because
gzip crushes exactly the repetition the raw figure is made of. The raw ceiling is the binding
one, so the keys are short and documented here instead.

**Terms are one flat array, not one per taxonomy.** Which taxonomy a term came from does not
change how a query matches it, and a second key per document buys nothing for ~5 KB raw. They
are de-duplicated: a post tagged `kubernetes` *and* filed under `Kubernetes` would otherwise
emit the term twice and have it counted twice by the scorer (2,309 term entries become 2,134 on
the reference archive).

### Code is never indexed

Not fenced blocks, not inline `` `code` `` spans, not the filename or language label the code
hook renders around them. Where a page has no `description`, the fallback strips
`<div class="rb-code-head">`, `<div class="rb-code-ui">`, `<pre>` and `<code>` from the rendered
content *before* plainifying it.

That is also why the fallback reads `.Content` rather than `.Summary`: Hugo's automatic summary
is the first ~70 words of **rendered** content, so a post that opens with a fence puts shell
commands straight into it.

### Drafts, future posts, and opting out

Excluded, and **explicitly** rather than by relying on the build flags:

- `.Draft` is checked directly. `site.RegularPages` already drops drafts — but only while
  nobody passes `-D`. A preview build with `--buildDrafts` would otherwise publish draft titles
  into a world-readable JSON file.
- `.Date` is compared against `now`, for the same reason with `-F`.
- A page can opt out of the index on its own:

  ```yaml
  ---
  title: "Sponsors"
  searchExclude: true
  ---
  ```

Only pages in `params.mainSections` are considered at all.

---

## The budget, and what was rejected

The budget is **≤ 250 KB raw / ≤ 60 KB gzipped** ([005 §3.1](../specs/005-performance-budgets.md)).
Every number below was produced by building **this theme** against the real 497-post reference
archive (490 published), `hugo --gc --minify`, compressed with `gzip -n -9`.

| Index shape | Raw | Gzip | |
|---|---:|---:|---|
| **Shipped** — title + URL + date + terms + summary(160) | **177,615** | **41,211** | 71% / 69% of budget |
| … + H2 headings | 271,868 | 62,656 | **over both** |
| … + H2 and H3 headings | 336,448 | 78,950 | **over by 35% / 32%** |
| Full text, as the incumbent theme ships it today | 4,551,252 | 1,256,759 | **18× / 21× over** |

**Headings are rejected.** They were the tempting half of open decision #5 — the archive has
3,250 H2 and 2,097 H3, they are genuinely good search signal, and a reader looking for "install
redis on rocky" is usually looking for a *section*. They do not fit. H2 alone is over the raw
ceiling by 21,868 B and the gzipped one by 2,656 B; H2 and H3 together are over by a third.

A per-post cap does not rescue it either. Capping at the first 8 H2s per post measures
**256,753 raw / 59,068 gz** — still over the raw ceiling, and with 932 B of gzip headroom left
for an archive that grows by one post. So the choice is not "headings, tuned" versus "no
headings"; it is "no headings" versus "no summaries", and summaries win because they are what a
result row has to show anyway.

**Full text was never a candidate.** [001 §2](../specs/001-overview.md) puts it out of scope
and the last row of that table is why: getting 4.55 MB of prose under a 250 KB budget needs a
build-time index compiler from npm, which [ADR-1](../specs/006-architecture-decisions.md)
rejects for a drop-in theme.

### `summaryLength` is the lever, not a cosmetic setting

The reference site sets `description` on 100% of its posts and caps them at 160 characters, so
its own index barely moves between `summaryLength = 160` and `= 240`. A site that does *not*
write descriptions falls through to the page content, and **that** is where the budget goes.
Both columns below are real builds of the same 490 posts, the right-hand pair with every
`description:` line stripped from the front matter:

| `summaryLength` | With `description` (raw / gz) | Without any `description` (raw / gz) |
|---:|---:|---:|
| 0 (no summaries) | 99,423 / 18,766 | 97,461 / 18,605 |
| 120 | 161,406 / 35,242 | — |
| **160 (default)** | **177,615 / 41,211** | **179,196 / 39,727** |
| uncapped | 177,615 / 41,211 | **2,319,355 / 646,771** |

The bottom-right cell is the point of the whole setting: with no `description` and no cap, the
index is the entire archive as plain text — 9.3× the raw budget. The cap is what makes the
budget **insensitive to whether the consumer writes descriptions at all**, which matters
because a theme cannot make them.

### How big an archive fits

Extrapolating the shipped shape linearly from 490 posts, the **raw** ceiling binds first:

| | Posts that fit |
|---|---:|
| `summaryLength = 160` | **~690** |
| `summaryLength = 120` | ~760 |
| `summaryLength = 0` | ~1,230 |

Past that, drop `summaryLength` first. Past ~1,200 posts a metadata index is no longer the right
architecture and a hosted search service is.

---

## The JavaScript

**A separate lazy chunk, loaded only on `/search/`.**

| | |
|---|---:|
| Budget | 3,000 B gz |
| **Measured** | **3,069 B raw / 1,416 B gz** |

`assets/js/runbook.js` is frozen at three modules and everything reachable from it shares one
3,000 B budget ([contracts §2.3](contracts.md#23-javascript)). Search has its own entry, its own
`js.Build` call in `_partials/search/js.html`, and its own budget. It is emitted from
`layouts/search.html` only, so the `<script>` tag exists on exactly one page. Verified, not
assumed:

```bash
grep -rlE '<script[^>]+js/search' public/ | grep -v '^public/search/'   # empty
```

### Effect on every other page

Measured by building the exampleSite twice, once with `search.enable = true` and once `false`,
and diffing:

| | |
|---|---|
| CSS bundle fingerprint | **identical** — `search.css` is in the bundle either way |
| `runbook.js` fingerprint | **identical** — search never entered the core chunk |
| Extra `<script>` tag on a non-search page | **none** |
| Extra request on a non-search page | **none** |
| Extra bytes on 24 of 35 pages | **+49 raw** — the header nav link, which is the feature |
| Extra bytes on the homepage | **+240 raw** — that link plus the JSON-LD `SearchAction` |
| Extra bytes with search off (the default) | **0** |

The index itself is never fetched until someone types, so landing on `/search/` costs zero
index bytes too.

### Script-tag count on `/search/`

`/search/` carries three executable scripts — the inline theme guard, `runbook.js`, and this
chunk — against the "≤ 2 per article" budget in [005 §3.1](../specs/005-performance-budgets.md).
That budget is stated per *article* and `scripts/check_budgets.py` enforces it over the shell
fixture and every built article page; `/search/` is neither. The only way to get to two is to
drop `runbook.js` from the page, which leaves the theme toggle dead on it. Recorded here so it
is a decision rather than a rediscovery.

### CSS

`search.css` stays in the single shared bundle rather than being split out for one page. It
takes the minified bundle from 16,669 → 19,042 raw and **4,036 → 4,371 gzipped**, so it costs
335 B gz on every page against an 8,000 B budget with 3,629 B spare. A separate stylesheet would
save those 335 B everywhere but cost a render-blocking round trip on the one page that needs it.
Re-check the trade if the file grows past a few hundred bytes gzipped.

---

## Cache policy

The chunk requests the index as `/search/index.json?v=<site.Lastmod as a Unix timestamp>`.

`site.Lastmod` moves when content changes and on nothing else, so:

- **Serve `/search/index.json` with a long `max-age`.** Publishing any content change moves the
  query string, and the next visitor misses the old cache entry.
- The JSON file itself is not fingerprinted, because it is an output format rather than a
  pipeline resource, and its URL is fixed by the migration-parity requirement above.
- The chunk fetches with `credentials: 'same-origin'` and no cache override, so the browser HTTP
  cache is the only cache. Nothing is written to `localStorage` or `sessionStorage`.

---

## Ranking

There is no stemmer, no inverted index and no BM25 — over 490 documents of about 200 characters
each, a linear scan with `indexOf` runs in well under a millisecond, and every byte spent on
cleverness comes out of the 3,000 B budget.

- The query is split on **whitespace only**. `c++`, `ci/cd`, `nginx.conf` and `k8s-node` are
  exactly the queries this corpus attracts, and a `\W` split makes every one of them match
  worse.
- **All terms must match** (AND). With fields this short, OR returns most of the archive for a
  two-word query.
- Per term: title prefix **10**, title word **8**, title substring **5**, taxonomy term **4**,
  summary **1**.
- Ties break on date, newest first. A 2024 answer usually supersedes the 2021 one.
- `maxResults` caps what is rendered; the status line still reports the true total.

---

## Without JavaScript

Success criterion 6 ([001 §5](../specs/001-overview.md)) is that every page is readable and
navigable with JavaScript disabled. For a search page that means **never an input that silently
does nothing**.

`assets/css/search.css` — not the JavaScript — is what guarantees it:

```css
.rb-search-form,
.rb-search-status,
.rb-search-results { display: none; }

.rb-search[data-rb-ready] .rb-search-form { display: flex; }
```

The form is hidden by default and the chunk sets `data-rb-ready` on the root once it has wired
the input up. `display: none` rather than `visibility` or `opacity`, so the input leaves the tab
order and the accessibility tree together.

What a reader sees in each state:

| State | What renders |
|---|---|
| JavaScript on, everything works | Input, live status line, results |
| **JavaScript off** | The `<noscript>` line "Search needs JavaScript. Browse by tag or category instead." plus the browse list. No input |
| **The chunk 404s or throws** | No input, no message — but the browse list is still there, because it is server-rendered and unconditional |
| The index fetch fails | "Search could not load. Browse by tag or category instead." |
| `search.enable = false` | "Search is not enabled on this site." plus the browse list |

The explanation lives in `<noscript>` specifically so it renders **only when it is true**: a
message that is visible by default and removed by JavaScript flashes on every page load for
everyone who has JavaScript.

The browse list is built from the site's own `mainSections`, any `layout: "archive"` page, and
every registered taxonomy — so it is correct for a consumer whose section is not `posts` and
whose taxonomy is not `tags`. It is rendered in **all** of the states above, including the
working one, because on a search page a list of links is useful anyway.

---

## Escaping — the one genuine XSS surface in the theme

Result titles, summaries and tags are author-controlled text that JavaScript writes into the
DOM. [008 M5](../specs/008-milestones.md) names search-result escaping in the security review.

The rule is structural, not a habit: **there is no `innerHTML`, `outerHTML`,
`insertAdjacentHTML` or `document.write` in `assets/js/search/`.** Every string reaches the page
through `textContent` or `document.createTextNode`. That includes the search-term highlighting,
which is where a naive implementation reaches for `replace(re, '<mark>$1</mark>')` and hands the
attacker the page; `mark()` splits the string and builds real `<mark>` elements around real text
nodes instead.

Link targets are validated too. `d.u` comes from Hugo's `RelPermalink` and cannot be hostile
today, but assigning an unvalidated string to `.href` is how that stops being true later, so
anything that is not a same-origin absolute path (`/^\/(?!\/)/` — rejecting `javascript:` and
protocol-relative `//host`) is dropped.

`exampleSite/content/posts/search-result-escaping.md` is the fixture. Its title is:

```
Escaping fixture: <script>alert("xss")</script> & <img src=x onerror=alert(1)> in a title
```

so on **every build** that string travels `layouts/search.json` → `/search/index.json` →
`fetch` → the scorer → the highlighter → the DOM. Two independent things have to hold, and they
fail differently: if Hugo's `jsonify` broke, the index would be invalid JSON and the page would
show its error state, which is loud; if the chunk's escaping broke, the index would still be
perfectly valid and the page would still look fine right up until it executed. The fixture is
aimed at the second.

Check it by hand after a build:

```bash
# The index carries the markup as DATA, escaped by jsonify:
python3 -c "import json;print([d['t'] for d in json.load(open('public/search/index.json'))['docs'] if 'script' in d['t']])"

# The built chunk contains no markup sink at all:
grep -cE 'innerHTML|outerHTML|insertAdjacentHTML|document\.write' public/js/search/*.js   # 0
```

Then open `/search/?q=escaping` and confirm the title renders as literal text, with no alert and
no injected element. As delivered, the title arrives as two DOM nodes —
`<mark>Escaping</mark>` and one text node containing the rest verbatim — which reassemble
byte-for-byte into the source title.

---

## Configuration reference

All under `params.runbook.search`.

| Key | Default | Effect |
|---|---|---|
| `enable` | `false` | Emits the index, the header link, the JSON-LD `SearchAction` and the chunk. Off, `/search/` still builds and shows the browse list |
| `summaryLength` | `160` | Characters of summary per document. **`0` drops summaries entirely** — see the budget table. This is the lever a large archive pulls |
| `taxonomies` | `["tags", "categories"]` | Which taxonomies contribute terms. A theme cannot register a taxonomy, so a site whose terms live under `topics` has to be able to say so |
| `maxResults` | `30` | How many results render. The status line still reports the true total |

Front matter:

| Key | Effect |
|---|---|
| `searchExclude: true` | Keeps a single page out of the index |
| `outputs: ["html", "json"]` | **Required on the search page.** This is what emits `/search/index.json` |

`0` is a meaningful value for `summaryLength`, so it is resolved with `isset` rather than
`| default` — `0 | default 160` is `160`, and a consumer who asked for no summaries would
silently get them.

### Strings

Every string comes from `i18n/en.yaml` under `# ── Search ──`. The chunk receives them as
`data-*` attributes rather than carrying literals.

`searchResultsOther` and `searchResultsCapped` contain `{n}` and `{m}` placeholders that the
**chunk** substitutes in the browser — they are not Hugo template syntax, and a translation that
drops them loses the number. Hugo's `.Count` pluralisation is not used because the count is only
known client-side.

---

## Overriding

Copy any of those files into your own `layouts/` or `assets/` and Hugo's lookup prefers yours.
Two things to keep if you do:

- **Never build result markup from strings.** See the escaping section.
- **Keep the form hidden by default.** If you re-style `search.css`, the `display: none` default
  is the whole zero-JavaScript guarantee; a rule that shows the input unconditionally puts a dead
  control in front of every reader without JavaScript.
