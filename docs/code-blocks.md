# Code blocks

Runbook's differentiating feature. Requirements are [003 §3.3](../specs/003-design-spec.md)
REQ-CB-1 … REQ-CB-8; verified Hugo behaviour is
[contracts §3](contracts.md#3-verified-hugo-behaviour).

Three files implement it and nothing else touches it:

| File | Does |
|---|---|
| `layouts/_markup/render-codeblock.html` | Builds the Chroma options, emits the wrapper and the controls |
| `assets/css/code.css` | Every visual rule, including the bare `pre > code` base case |
| `assets/js/modules/code.js` | Copy, wrap toggle, overflow detection |

---

## Author-facing attributes

Hugo's canonical lowercase names, so this documentation matches upstream examples.

| Attribute | Effect |
|---|---|
| ` ```bash {linenos=true} ` | Line numbers for this block only |
| ` ```bash {hl_lines="2-4"} ` | Highlight lines |
| ` ```yaml {file="docker-compose.yml"} ` | Filename label — this is what triggers the header bar |
| ` ```sh {caption="Run on every worker"} ` | Caption — also triggers the header bar |
| ` ```console {prompt="$"} ` | Prompt-aware copy |
| ` ```text {output=true} ` | Command-output treatment (or tag the fence ` ```output `) |

`linenos` and `hl_lines` are known to Chroma and arrive in `.Options`. `file`, `caption`,
`prompt` and `output` are not, and arrive in `.Attributes`. The hook reads each from the
correct place; they are not interchangeable ([004](../specs/004-hugo-mechanics.md) §1).

---

## Chrome appears only when it has something to say

**No block gets a header bar by default.** Every block gets a muted corner language tag and a
copy control. A bar appears only when there is something to put in it — a `file=`, a
`caption=`, or both. Line numbers do not trigger one.

This is not an aesthetic preference. In the reference corpus **45.2% of blocks are exactly one
line and 57.0% are two lines or fewer**, so a conventional docs-style header — language label,
filename, copy button — is *taller than its own content* on the majority of blocks. And at 18.2
blocks per post, a rule that switches chrome on at some line count makes the chrome flicker on
and off down the page.

The rejected alternative was a threshold: no header under three lines, full header at three or
more. It fails on its own terms at this distribution — the "exception" is the majority case —
and it bakes in a magic number that had already had to move once before it was written down.

**The warm redesign did not move this trigger, and it was never in conflict with it.** The design
draws every code block with a filename bar, and it can, because every block it draws *has* a
filename: `baseline.sql`, `postgresql.conf`, `vacuum.sh`. `{file=…}` is exactly what raises the
bar here. What was adopted was the bar's *styling* — it is now part of the plate rather than a
separate box sitting on top of it, sharing the plate's background and separated by a hairline —
and a one-line block still gets the corner language tag, the ghost copy control, and no bar.

---

## What the copy button copies

The `<code>` element's `textContent`, with line endings normalised to `\n` and **at most one**
structural trailing newline removed. That is all. Specifically:

- **Line-number gutters are never copied.** In table mode Chroma puts them in a separate
  `<td>`; the copy reads `code[data-lang]`, which is the other cell. They are also
  `user-select: none`, so a manual drag-select does not pick them up either.
- **The code is not duplicated into a `data-` attribute.** At 9,046 blocks that roughly doubles
  the code bytes in the HTML. Chrome markup repeats and so costs almost nothing after gzip
  (measured: 18 blocks of controls = 7,434 raw bytes but **223 gzipped**); code does not repeat,
  so gzip cannot absorb a second copy of it.
- Copying is announced through a single page-level `aria-live="polite"` region, and the button
  shows a check mark for 1.6 s.
- Copy is independent of visual wrapping. Turning the wrap toggle on never changes what you get.

### Why `$ ` is never stripped heuristically

**1,389 lines across 318 posts — 64% of the reference archive — begin with `$ `.** Mixed
command-and-output blocks are routine, `#` may be a real shell comment rather than a root
prompt, and `$` may be data (`echo $HOME`, a price, a regex). Any content-sniffing rule is
wrong on a large number of real blocks, and when it is wrong it silently hands the reader a
command that is not the command.

So stripping is an explicit per-block opt-in and is **never** inferred:

````markdown
```console {prompt="$"}
$ systemctl status redis
● redis.service - Redis persistent key-value database
$ redis-cli ping
PONG
```
````

Copying that yields exactly:

```
systemctl status redis
redis-cli ping
```

The rules, in full:

- The prompt must be the first non-whitespace text on the line, so `echo $HOME` is not treated
  as a prompt line.
- One space after the prompt is consumed, if present.
- A line ending in `\` keeps its continuation lines verbatim, so a wrapped `kubeadm join` copies
  whole rather than as its first line.
- If no line matches the prompt, the whole block is copied unchanged rather than nothing. That
  is also what happens to a `[root@host ~]#` style prompt: the prompt token is not at the start
  of the line, so declare the literal prefix you actually use, or leave the block alone and let
  it copy verbatim.

### When the clipboard is unavailable

The async Clipboard API is used when it exists. Otherwise the copy falls back to a detached
`<textarea>` and `document.execCommand('copy')` — a textarea rather than a selection over the
code element, because prompt-filtered text is not what is on screen.

If neither path exists the copy buttons are **never unhidden**. If a copy is attempted and both
paths fail, the button announces the failure and then hides itself. A control that cannot work
is not presented.

---

## Scrolling, wrapping, and the tab stop

**Long lines scroll horizontally. They never wrap by default.** 1,586 blocks (17.5%) contain a
line over 80 characters and the longest is 854. Soft-wrapping a `kubeadm join` silently changes
what the reader believes the command to be, so the wrapped rendering has to be something the
reader asks for.

The wrap toggle carries `aria-pressed` and appears **only on blocks that actually overflow**.
It is **session-local and deliberately not persisted**: wrapping is a property of the one long
line being inspected, not a reading preference. Persisting it would re-break the next command
the reader copies by eye, on a page they have not opened yet.

Native scrollbars are kept.

### `tabindex` is applied by measurement, not by markup

Chroma emits `<pre tabindex="0">` on every block unconditionally, and exposes no option to
suppress it. The hook strips it, and `code.js` re-adds it only to blocks whose scroll width
actually exceeds their client width — measured on load, on resize, and after webfonts settle,
because overflow depends on viewport and font metrics and cannot be known at build time.

At 18.2 blocks per post an unconditional tab stop per block is a real navigation tax, and
Chrome 127+ already makes scroll containers focusable without help.

A wrapped block does not overflow, so it gives up its tab stop while keeping its wrap button.

### Two implementation details worth knowing before editing `code.css`

**The inline-end reserve is on the `<code>`, not the `<pre>`.** Padding on the inline-end of a
horizontal scroll container is not part of its scrollable overflow: a line running into that
padding neither pushes it along nor raises `scrollWidth`. Measured in Chrome at 360 px,
`sudo dnf -y install redis` had its last 10 px sitting under the copy button while
`scrollWidth === clientWidth` reported nothing to scroll. `width: max-content` on the `<code>`
plus `padding-inline-end` puts the reserve after the longest line, where it counts.

**In line-number mode the wrapper scrolls, not the `<pre>`.** A `<td>` grows to fit its
content, so a scroll container inside one never gets a constrained width to scroll against; the
table simply widened and the overflow was clipped by the wrapper — invisible *and* unreachable.
`div.chroma` is therefore the scroll container for that shape, and `code.js` measures
`code.closest('div.chroma') || code.parentElement`. The gutter scrolls away with the code,
which is the accepted cost.

Below 30 rem the language tag is hidden and the reserve shrinks to the two buttons. At 310 px of
column, holding the desktop reserve turns the most common block shape in the corpus into a
scroll container. This is a viewport rule, not a per-block threshold, so adjacent blocks always
agree with each other.

---

## The plate is dark in both themes

`--rb-code-bg` is `#211f1b` in the light theme and `#171512` in the dark one. The block is the
darkest, most saturated object on a cream page rather than a lightly-tinted rectangle of it, and
the corpus is the argument: 9,046 fenced blocks, zero Markdown body images. There is one picture
on the page and it is the code.

Two consequences worth knowing about if you restyle:

- **`scripts/check_contrast.py` asserts the light theme's syntax palette against a dark plate**,
  because it resolves the plate from the token rather than from the theme name. Retuning
  `--rb-code-bg` in your own CSS moves what the gate would check, but the gate reads the *theme's*
  CSS — an override is unverified until you check it yourself.
- **Nothing inside a block may take a page-level colour any more.** `--rb-color-text-muted` is
  near-black in the light theme; so is the plate. Inside `.rb-code`, use `--rb-code-text`,
  `--rb-code-chrome-fg` or a `--rb-syn-*` role — the pairs the gate actually asserts.

Highlighted lines now draw `--rb-code-hl-border` as an inline-start marker
(`box-shadow: inset`, not a border, so the line's text does not shift). That is the conformant
WCAG 1.4.11 signal; the background tint only reinforces it.

---

## Command output

Muted, unhighlighted, no copy button, and **explicitly asked for**:

````markdown
```text {output=true}
● redis.service - Redis persistent key-value database
     Active: active (running) since Tue 2026-07-28 09:14:22 UTC; 3h ago
```
````

` ```output ` as the fence language does the same thing.

Output blocks are rendered through the plaintext lexer whatever language they were tagged with,
which is the point: **with `guessSyntax: true` an untagged block of terminal output receives
speculative token colours**, and this treatment exists to stop that. The hook passes
`guessSyntax: false` explicitly on every call, so the consumer's setting cannot reintroduce it.

Output blocks take `--rb-code-chrome-fg` on `--rb-code-output-bg` — the theme's "quiet foreground
inside the plate", which the contrast gate asserts against that background specifically — plus an
olive inline-start rail as a second, non-colour signal that this is output rather than a command
to run.

**Do not** expect `text` or untagged fences to be styled as output automatically. They are not,
and they must not be: `text` grew from 119 to 426 blocks in the reference corpus and many of
those are configuration files, not output.

---

## Line numbers cannot be turned on site-wide

`markup.highlight.lineNos` and `lineNumbersInTable` in a consuming site's configuration have no
effect on Runbook's code blocks. This is deliberate and it is the single most important rule in
the theme.

`transform.Highlight` applies the *consuming site's* settings for any key the caller leaves
unset, and Hugo merges theme configuration *underneath* site configuration — so a theme cannot
fix this by shipping a saner default. The reference site sets both keys to `true` today, and
that is what puts a line-number gutter on a one-line `sudo dnf -y install redis` across 484
pages.

The hook therefore builds its option set from scratch and passes every **structure-changing**
key on every call, not only when the value is true:

`lineNos` · `lineNumbersInTable` · `anchorLineNos` · `lineNoStart` · `hl_lines` · `hl_inline` ·
`noClasses` · `guessSyntax` · `wrapperClass`

Colour-only keys (`style`, `tabWidth`) are left alone. A consumer retuning colour is not a bug;
a consumer restructuring the theme's markup is.

CI asserts this by building `exampleSite` twice and diffing:

```bash
hugo --source exampleSite --themesDir ../.. --destination ../public-test --cleanDestinationDir
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true \
  hugo --source exampleSite --themesDir ../.. --destination ../public-hostile --cleanDestinationDir
diff -r ../public-test ../public-hostile
```

The two trees must be identical. **Site configuration is untrusted input to a distributable
theme.**

To use line numbers, opt in per block with `{linenos=true}`.

---

## Language labels

`sh`, `bash`, `zsh`, `ksh` and `shell` are all aliases of Chroma's one Bash lexer, so all 7,143
shell-family blocks in the corpus already highlight identically. There is nothing to normalise.

The only work is cosmetic: a display map in the hook so the corner tag reads `Shell` rather than
`sh` and `YAML` rather than `Yaml`. Anything not in the map falls through to title case, which
is right for `python`, `nginx`, `terraform` and the 36-language tail. The author's fence
language is never rewritten — `data-rb-lang` and the `language-*` class carry it verbatim.

An untagged fence gets no tag at all rather than a speculative one.

---

## Indented code has no controls, and cannot have them

Four-space-indented code **bypasses the render hook in every Hugo version**. No copy button, no
language tag and no wrap toggle is possible there, so CSS is the only tool that reaches it —
which is why `pre > code` is the styled base case (REQ-CB-8) and `.highlight` is the *enhanced*
case that only adds token colour on top.

The two are visually identical: same padding, radius, background, border, font, line height,
`tab-size` and overflow behaviour. This is asserted, not assumed — computed styles for the
indented block on the smoke-test page match the enhanced blocks property for property.

The same base case covers two more shapes a theme cannot prevent:

- a consumer with `markup.highlight.codeFences: false`, or `guessSyntax: false` on an untagged
  fence;
- **a fence whose language Chroma has no lexer for.** Hugo then emits
  `<pre tabindex="0"><code class="language-X">` with no `class="chroma"` and no `.highlight`
  wrapper at all. The hook strips that `tabindex` too, and every selector in `code.css` keys on
  `.rb-code pre` rather than `pre.chroma` so the shape is styled like any other.

---

## WordPress-migrated markup

Runbook does **not** ship `.wp-block-code` / `.wp-block-preformatted` styling. The reference
archive now contains zero instances, and `goldmark.renderer.unsafe: false` escapes such markup
anyway — it is no longer a demonstrable claim, so it is documentation rather than shipped bytes
(ADR-3).

If you are migrating a site that still contains it, add this to your own CSS:

```css
.wp-block-code,
.wp-block-preformatted {
  margin: 0 0 var(--rb-space-5);
  padding: var(--rb-space-4);
  background: var(--rb-code-bg);
  color: var(--rb-code-text);
  border: 1px solid var(--rb-code-border);
  border-radius: var(--rb-radius-code);
  overflow-x: auto;
  font-family: var(--rb-font-mono);
  font-size: var(--rb-text-code);
  line-height: var(--rb-leading-code);
}
```

You will also need `goldmark.renderer.unsafe: true` for the raw HTML to render at all. Prefer
converting the blocks to fences: they then get the copy button, the language tag and the wrap
toggle, and none of this CSS is needed.

---

## Without JavaScript

Every block is fully readable and fully scrollable. Both controls are rendered `hidden` by the
hook and unhidden by `code.js`, so **no dead control is ever shown** — verified with script
execution disabled: 16 controls in the DOM, 16 of them `hidden`, no `tabindex`, no live region.

Note that `[hidden]` in the UA stylesheet is a bare element selector and loses to
`.rb-code-btn { display: inline-flex }`. `code.css` restates
`.rb-code-btn[hidden] { display: none }` for exactly this reason; removing it presents every
control to every reader with JavaScript off.

---

## Overriding

The theme's own styling lives on `.rb-code` and its children. To restyle without forking the
hook, target:

| Selector | Is |
|---|---|
| `.rb-code` | The block wrapper. Carries `data-rb-lang`, and `data-rb-head` / `data-rb-output` / `data-rb-prompt` when they apply |
| `.rb-code-head` | The header bar, present only with `file=` or `caption=` |
| `.rb-code-ui` | The corner row |
| `.rb-code-lang` | The language tag |
| `.rb-code-btn`, `.rb-code-copy`, `.rb-code-wrap` | The controls |
| `.rb-code[data-rb-wrapped]` | A block the reader has turned wrapping on for |
| `.rb-card-plate` | Not part of a block at all: the code plate `list/post-item.html` draws on a list card, from that post's first fence. Capped at four lines, truncated rather than scrollable, `aria-hidden`, and it strips Chroma's `tabindex` for the same REQ-CB-6 reason the hook does |

Chroma's own classes are unchanged: `.highlight`, `.chroma`, `.line`, `.cl`, `.lntable`, `.lnt`.
Highlighted lines are `<span class="line hl">` on the code side and a bare `<span class="hl">`
in the line-number gutter — a bare `.hl` selector matches only the gutter, which is a good way
to highlight a line number and not its line.
