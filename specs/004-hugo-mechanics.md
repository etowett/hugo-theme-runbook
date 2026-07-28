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
