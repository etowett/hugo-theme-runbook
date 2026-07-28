---
name: code-block
description: The measured contract behind Runbook's code-block render hook — why it never trusts site config, the Chroma behaviours that are not in the documentation, and what REQ-CB-1 actually proves. Use before editing layouts/_markup/render-codeblock.html, assets/css/code.css or assets/js/modules/code.js, or when a fenced block renders with line numbers, a stray tabindex, wrong highlight styling or unexpected chrome.
allowed-tools: Read Grep Glob Bash(hugo *) Bash(python3 *)
---

# The code block

**The code block is the product.** 9,046 fenced blocks across 497 posts — 18.2 per post, 79%
shell, **45.2% exactly one line**. That last number is the design constraint: chrome must never
exceed content height, so no block gets a header bar unless `file=` or `caption=` gives it
something to put in it. A bar-by-default is taller than its own content on the majority of blocks
and flickers on and off down the page.

Owned files: `layouts/_markup/render-codeblock.html`, `assets/css/code.css`,
`assets/js/modules/code.js`, `docs/code-blocks.md`. Read
[docs/code-blocks.md](../../../docs/code-blocks.md) for the consumer-facing attribute reference;
this file is the part that is not obvious from the markup.

## 1 — the hook must never trust site config

`transform.Highlight` inside a render hook applies the **consuming site's** `markup.highlight`
defaults for any key the caller leaves unset, and Hugo merges theme config *underneath* site
config — so a theme default cannot fix it.

The reference site sets `lineNos: true` today. That is what puts a line-number gutter on a
one-line command across 484 pages.

**The hook therefore passes `lineNos` and `lineNumbersInTable` on every call, not only when
true.** An unset key is exactly where the consumer's configuration gets back in. If you are
editing the option map and a key looks redundant because it is being set to its own default,
that is the key holding the door shut.

`.Options` itself is safe to read: measured on v0.164.0+extended against a site forcing
`lineNos=true, lineNumbersInTable=true`, a block that did not opt in reported `map[hl_lines:3-4]`
with **no `linenos` key**, while a block carrying `{linenos=true}` reported `map[linenos:true]`.
So `.Options` is fence-only and does not merge site config. The leak is inside
`transform.Highlight`, not in the attribute plumbing.

### What REQ-CB-1 proves, and what it does not

`scripts/check_reqcb1.py` builds `exampleSite` twice — once normally, once with
`HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true` — and requires
the trees to be **byte-identical**. It is stricter than grepping for `lntable`, needs no pinned
content, and runs on every pull request.

It proves output does not *change*. It does not prove the theme still *builds* under the other
settings a consumer might force, where output legitimately differs so an identity diff is the
wrong test — that is the separate "hostile consumer configuration" step in `/gates`
(`noClasses`, `guessSyntax`, `unsafe`).

## 2 — Chroma behaviours that are not in the documentation

Measured against `exampleSite`, 2026-07-28, on v0.164.0+extended:

- **Chroma emits `<pre tabindex="0">` unconditionally**, which contradicts REQ-CB-6. There is no
  `transform.Highlight` option to suppress it. The hook strips it, and the JavaScript re-adds it
  **only to blocks that actually overflow** — a focus stop on a block nobody can scroll is a
  keyboard trap for no benefit.
- **Highlighted lines are `<span class="line hl">`.** A bare `.hl` selector matches nothing.
- **Attribute routing:** Chroma-known keys (`linenos`, `hl_lines`) land in `.Options` with
  **lower-cased** names. Unknown keys (`file`, `prompt`, `output`) land in `.Attributes` with
  their original spelling. Reading the wrong map is silent — you get an empty string, not an
  error.

## 3 — two bugs that were invisible in the markup

Both were found by driving a browser, and both are the reason this repository's rule is *measure
rather than assert*:

- **`padding-inline-end` does not count toward scrollable overflow.** A block that looked padded
  and scrollable clipped its last characters instead.
- **A `<td>` grows to its content, so an inner `<pre>` never gets a width to scroll against.** A
  code block inside a table stretched the table instead of scrolling. `/posts/tables-and-data/`
  is the regression fixture for it.

If a change touches overflow, padding, focus order, the copy button or the wrap toggle, **look at
it in a browser** — `/serve`, then `/posts/code-block-767-lines/`, `/posts/tables-and-data/` and
`/posts/code-blocks-158/`. `.mcp.json` wires up Playwright for this.

## 4 — the copy and wrap behaviour

- **Horizontal scroll, never soft wrap by default.** Wrapping a `kubeadm join` silently changes
  what the reader believes the command to be. The wrap toggle appears only on blocks that
  actually overflow.
- **The copy button works on touch and by keyboard**, and `{prompt="$"}` copies the commands out
  of a mixed command-and-output block, leaving the output behind.
- Icons are hand-authored SVG path data inlined as `mask-image` data URIs in `code.css`. **No
  icon font, no icon library, no third-party request** — do not add one.

## 5 — budget

Everything reachable from `assets/js/runbook.js` shares **one 3 KB gzipped budget**, and that
file is frozen at three modules: own `modules/code.js`, not the entry point. Measure with
`gzip -n -9` — without `-n`, gzip writes an mtime into the header and the budget gate goes flaky.

## Before you finish

`/gates`, and quote `check_reqcb1.py`'s result explicitly. It is the strictest thing in CI and it
is the one that fails when the option map has been "tidied up".
