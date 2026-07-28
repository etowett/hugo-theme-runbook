# 004 — Hugo mechanics: verified behaviour the theme depends on

**Status:** verified empirically
**Date tested:** 2026-07-28
**Hugo version:** v0.164.0+extended+withdeploy darwin/arm64

---

## Why this document exists

Three of Runbook's central design decisions rest on assumptions about how Hugo's code-block render
hook behaves. Those assumptions are load-bearing enough that they were tested rather than read.
This document records what a purpose-built test site actually produced.

**Test method.** A minimal Hugo site with one content file containing five distinct code
representations, and a `render-codeblock.html` hook that reports what it receives
(`.Type`, `len .Attributes`, `len .Options`, `.Inner`).

---

## 1. Hook coverage — what fires and what does not

| Representation | Hook fires? | `.Type` value |
|---|---|---|
| ` ```bash ` fenced with language | **yes** | `"bash"` |
| ` ``` ` fenced, no language | **yes** | `""` (empty string) |
| `~~~` tilde fence, no language | **yes** | `""` |
| ` ```yaml {file="x" hl_lines="1"} ` | **yes** | `"yaml"` |
| **4-space indented code** | **NO** | — bypasses the hook, emits bare `<pre><code>` |

### Consequences

**Every fenced block is reachable.** All 9,046 fenced blocks in the citizix corpus — including the
93 that carry no language tag — pass through the hook. The complete code-block feature set (adaptive
chrome, copy button, wrap toggle, opt-in line numbers, filename label) therefore applies to 100% of
fenced content. There is no second code path to maintain for untagged fences.

**`.Type` is an empty string, not nil, for untagged fences.** The hook must handle `""` explicitly —
`{{ $lang := or .Type "text" }}` — or Chroma receives an empty lexer name.

**Indented code is architecturally unreachable.** No Hugo version routes indented code blocks
through `render-codeblock`. CSS-only styling is the hard ceiling for them: no copy button, no
language label, no wrap toggle is possible. This is why the theme must still style bare
`pre > code` as a base case — see §4 below.

**Attribute routing is split.** With `{file="docker-compose.yml" hl_lines="1"}`, the Chroma-known
key (`hl_lines`) arrives in `.Options` and the unknown key (`file`) in `.Attributes`. The hook must
read filenames from `.Attributes` and highlight options from `.Options`; they are not interchangeable.

---

## 2. `transform.Highlight` inside the hook inherits the CONSUMER's site config

This is the non-obvious finding, and it is a live trap.

A hook calling `transform.Highlight .Inner $lang .Options` against a site configured with:

```toml
[markup.highlight]
lineNos = true
lineNumbersInTable = true
```

produced `<table class="lntable">` with a line-number gutter for **every block, including one-line
blocks**. Four blocks in, four `lntable` wrappers out.

**citizix's own `config.yaml` sets exactly these two options today.** They are what produce the
484-page line-number-table problem in the current build.

A theme cannot fix this by shipping a saner default. Hugo merges theme configuration *underneath*
site configuration, so the consumer's value always wins. The only reliable fix is for the hook to
construct its own options and never forward the site's line-number settings.

### Requirement this generates

> **REQ-CB-1.** The `render-codeblock` hook MUST build the option set it passes to
> `transform.Highlight` explicitly, with `lineNos` forced off unless the individual block opted in
> via `{lineNos=true}`. It MUST NOT forward the site's `markup.highlight.lineNos` or
> `lineNumbersInTable` values. **Site configuration is untrusted input to a distributable theme.**

Issue #1 §2.1 proposed "Runbook defaults `lineNos: false`". That describes a config default, which
site config overrides — it would not have worked, and citizix would have carried its existing
line-number problem straight into the new theme.

The same principle generalises: any `markup.highlight` key that changes emitted *structure* rather
than emitted *colour* must be forced by the hook, not merely defaulted.

---

## 2a. `jsonify` inside a `<script>` block is double-encoded

**Added 2026-07-28 after this bug was found and fixed across all 493 article pages on the
reference site (citizix#61, citizix#62).** The spec calls for JSON-LD in
[003](003-design-spec.md) §3.7, so Runbook would have hit it too.

Go's `html/template` applies **contextual autoescaping**. Inside
`<script type="application/ld+json">` it treats the body as a JS context and re-escapes anything
written there — including output that is already valid JSON. So the natural-looking template:

```go-html-template
<script type="application/ld+json">
{
  "headline": {{ .Title | jsonify }},
  "datePublished": {{ .Date.Format "2006-01-02T15:04:05Z07:00" | jsonify }}
}
</script>
```

emits:

```json
{"headline":"\"How to Install Redis 6 on Rocky Linux 8\"","datePublished":"\"2026-03-04T10:00:00Z\""}
```

Every string value carries literal quote characters. The JSON still *parses*, which is why this
survives casual inspection — but `datePublished` is no longer a valid ISO 8601 date to any consumer,
and `headline` contains quotes a search engine will index.

On the reference site this affected **493 of 493 article pages** and every `jsonify`'d field:
`headline`, `description`, `author.name`, `author.url`, `publisher.name`, `datePublished`,
`dateModified`, `mainEntityOfPage.@id`, `keywords`, `articleSection`, `genre`.

### REQ-SEO-1 — build the object, serialise once

> Structured data MUST be assembled as a map and serialised in a single `jsonify`, with the result
> marked `safeJS`. Values MUST NOT be interpolated individually into a hand-written JSON literal.

```go-html-template
{{- $schema := dict
    "@context" "https://schema.org"
    "@type" "Article"
    "headline" .Title
    "datePublished" (.Date.Format "2006-01-02T15:04:05Z07:00")
-}}
<script type="application/ld+json">{{ $schema | jsonify | safeJS }}</script>
```

Both `| jsonify | safeJS` per field and the whole-object form produce correct output — verified on
Hugo v0.164.0. The whole-object form is required anyway because it makes recurrence *structurally*
impossible rather than depending on someone remembering a filter at each of eleven call sites, which
is exactly how the reference site regressed.

---

## 3. Hook file location and precedence

Hugo ≥ 0.146 resolves render hooks from `layouts/_markup/render-codeblock.html`. The legacy path
`layouts/_default/_markup/render-codeblock.html` also resolves, and **took precedence when both
existed** in testing.

> **REQ-CB-2.** Runbook ships the hook at `layouts/_markup/render-codeblock.html` only. Shipping
> both paths creates a silent precedence trap for consumers who override one and see no effect.

This also sets the floor for `min_version` in `theme.toml`.

---

## 4. Why bare `pre > code` styling survives — on new grounds

Issue #1 §3.4 justified styling bare `pre > code` with a corpus statistic: *"218 posts (43.9% of the
archive) render as unstyled `<pre>`."* After citizix PR #60 that number is **0%**, so the stated
justification is void.

The requirement survives for two different and more durable reasons:

1. **Indented code blocks bypass the render hook in every Hugo version** (§1). Any theme that styles
   only `.highlight` renders them unstyled. citizix has one such post left; third-party adopters
   will have more, and a theme cannot control their content.
2. **Third-party robustness.** Runbook is intended for general use. A WordPress-migrated site that
   has not run a cleanup will contain exactly the markup citizix just removed. Defensive styling for
   `.wp-block-code` and `.wp-block-preformatted` costs a few CSS selectors and makes the theme safe
   to drop onto such a site.

> **REQ-CB-3.** `pre > code` is the styled base case. `.highlight` is the *enhanced* case that adds
> token colour on top. The two must be visually identical apart from syntax colouring — same
> padding, radius, background, font, and overflow behaviour.

The change from issue #1 is one of **priority, not content**: this is no longer a citizix-blocking,
milestone-defining requirement. It is a robustness requirement that costs little and should not
gate the code-block milestone.

---

## 4a. Taxonomy term titles are derived badly, and `_index.md` is a trap

**Added 2026-07-28 from the reference site's taxonomy cleanup (citizix#63, #65, #72, #76).**

### Hugo capitalises each hyphen segment

A term with no `_index.md` gets its title from the term key with each hyphen-separated segment
capitalised. For a corpus that uses kebab-case terms — the normal convention — that produces:

| Term | Hugo renders | Should be |
|---|---|---|
| `alma-linux` | Alma-Linux | Alma Linux |
| `amazon-eks` | Amazon-Eks | Amazon EKS |
| `sql-server` | Sql-Server | SQL Server |
| `github-actions` | Github-Actions | GitHub Actions |
| `ci-cd` | Ci-Cd | CI/CD |
| `infrastructure-as-code` | Infrastructure-as-Code | Infrastructure as Code |

This is the term page's `<title>` **and** its on-page heading — the first thing a reader sees.

The reference site now carries **83 taxonomy `_index.md` files, 60 of which exist solely to
override a display title**. That is pure boilerplate every consumer of any theme has to write.

> **REQ-TAX-1.** Runbook renders term titles through a partial that (a) replaces hyphens with
> spaces and title-cases, and (b) consults an optional site-configurable acronym/spelling map
> (`params.taxonomyTitles`) for cases capitalisation cannot infer — `EKS`, `SQL`, `GitHub`,
> `CI/CD`, `cert-manager`. A term's own `_index.md` `title` always wins.

This turns 60 files of boilerplate into a handful of config entries, and it is a genuine
differentiator: no widely-used Hugo theme does it.

### A term `_index.md` keeps the page alive at zero posts

Verified the hard way: after removing a tag from every post that used it, the term page kept
building — because an `_index.md` for that term still existed. The result was an orphaned page
listing nothing, rather than the intended redirect.

> **REQ-TAX-2.** Document this in the theme's taxonomy guide. Retiring a term means deleting its
> `_index.md`, not just removing the term from front matter. Any redirect must live on the
> *surviving* term's `_index.md` as an `aliases` entry.

The theme cannot prevent it, but every consumer merging duplicate terms will hit it.

---

## 5. Implication for the article-HTML budget

Because the hook receives raw `.Inner` and the theme calls `transform.Highlight` itself, **the theme
controls Chroma markup volume** — it is not fixed overhead imposed by Hugo.

Dropping `lineNumbersInTable` alone removes one `<table>`, one `<tr>`, two `<td>` and one `<pre>`
per block. At a measured 18.2 blocks per post, that is the single cheapest lever available against
the article-HTML budget, and it is entirely within the theme's control.

Measured on the current citizix build, sampled article
`how-to-merge-multiple-kubeconfig-files-into-one/index.html`, compressed with `gzip -n -9`:

| Variant | Raw | Gzip |
|---|---:|---:|
| As built today | 34,109 | 8,091 |
| Remove line-number tables | 31,984 | 7,982 |
| Remove JSON-LD `articleBody` only | 30,363 | 7,659 |
| Remove all JSON-LD | 29,111 | 7,327 |
| Remove line-number tables **and** `articleBody` | 28,238 | 7,541 |

Note that line numbers are **not** the largest lever. citizix's local
`layouts/partials/head/schema.html:52` emits the entire article plaintext a second time as
JSON-LD:

```go-html-template
"articleBody": {{ $.Plain | jsonify }},
```

Removing that saves more bytes (432 B gz) than removing every line-number table (109 B gz). Both are
worth doing, and neither is imposed by Hugo — but it means the claim "Chroma markup is most of the
article page" is false. See [005 — Performance budgets](005-performance-budgets.md).
