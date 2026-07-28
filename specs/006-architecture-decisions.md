# 006 — Architecture decisions and resolved questions

**Status:** decided
**Last revised:** 2026-07-28

---

## ADR-0 — Target Hugo's new template system; declare a version floor

**Decision.** Runbook targets the post-v0.146.0 template system and declares
`min_version = "0.146.0"` in `theme.toml`, with the practical development and CI target being the
latest release.

**Context.** Hugo v0.146.0 (April 2025) re-implemented the template system: `layouts/_default/` is
gone, `layouts/partials/` became `layouts/_partials/`, `single.html` became `page.html`, and
`index.html` became `home.html`. Old-style trees still resolve through a compatibility mapping, but a
greenfield 2026 theme has no reason to ship the legacy layout.

This also settles the render-hook path question empirically established in
[004](004-hugo-mechanics.md) §3: ship **only** `layouts/_markup/render-codeblock.html`. Shipping both
the new and legacy paths creates a silent precedence trap, since the legacy path wins when both
exist.

Note that the reference site is itself currently a half-migrated mixture — `layouts/_default/` and
`layouts/partials/` alongside `layouts/_partials/` and `layouts/home.html`. That is exactly the state
a new theme must not ship in.

**Issue #1 never mentioned a Hugo version floor anywhere**, including in its own `min_version`
checklist item. This was the largest architectural omission in the original proposal.

---

## ADR-1 — Vanilla CSS with custom properties; no Tailwind

**Decision.** Plain CSS with custom properties, assembled through Hugo's own pipeline
(`resources.Get | minify | fingerprint`), single stylesheet, zero external toolchain.

**Verified.** Hugo's documentation states that as of **v0.161.0** Hugo no longer supports the
Tailwind standalone binary, and the CLI must be installed via **npm**
([`css.TailwindCSS`](https://gohugo.io/functions/css/tailwindcss/)). For a distributable theme that
means every consumer needs Node just to build a blog, and so does the showcase demo builder.

**Framing correction.** State this as a *consumer-installation* decision, not as proof that Tailwind
is universally unsuitable. The argument is "no required Node toolchain for a drop-in theme", not
"Tailwind is bad".

---

## ADR-2 — Class-based Chroma with two scoped palettes

**Decision.** `markup.highlight.noClasses: false` so tokens carry classes; ship light and dark Chroma
palettes scoped under `:root[data-theme="…"]`.

Inline styles (`noClasses: true`) make dual-theme highlighting impossible without emitting every
block twice.

**Clarification on the original wording.** "Dual stylesheets" is not required — both palettes can
live in one fingerprinted CSS artifact under theme selectors, which is preferable for the request
budget. Document `noClasses: false` as a consuming-site requirement and fail or warn clearly if the
site uses inline Chroma styles.

---

## ADR-3 — `pre > code` is the base case; `.highlight` is enhancement

**Decision retained, justification replaced, priority downgraded.**

Issue #1 justified this with "218 posts, 43.9% of the archive, render as unstyled `<pre>`" and marked
it non-negotiable and milestone-defining. **That figure is now 0%** — see
[002](002-corpus-profile.md) §9.

The decision survives on two durable grounds:

1. **Indented code blocks bypass the render hook in every Hugo version**
   ([004](004-hugo-mechanics.md) §1). Any theme styling only `.highlight` renders them unstyled.
2. **Third-party robustness** — consumers with `guessSyntax: false` or
   `markup.highlight.codeFences: false` produce bare `pre > code` routinely.

**What changes:** this is now a ~200-byte robustness clause, not a differentiator. It does not gate
the code-block milestone. And the `.wp-block-code` / `.wp-block-preformatted` defensive CSS is
**cut** — zero instances remain in the reference archive, `unsafe: false` escapes such markup anyway,
and "safe to drop onto a WordPress-migrated site" is no longer a demonstrable claim. Offer it as a
documented snippet in the migration guide instead.

---

## ADR-4 — `color-scheme` + `data-theme` + custom properties

**Decision.** Use `:root[data-theme]` custom properties as the primary mechanism, set `color-scheme`
so native form controls and scrollbars follow, and inline a tiny blocking script in `<head>` that
stamps `data-theme` from `localStorage` before first paint to prevent the theme flash.

**The original rationale was partly wrong and is replaced.** Issue #1 argued that `light-dark()`
"does not express a persisted three-way auto / light / dark toggle". That is false — stamping
`data-theme` and setting `:root[data-theme=dark] { color-scheme: dark }` forces `light-dark()` to
resolve dark, which is precisely the technique in the
[pepelsbey.dev article](https://pepelsbey.dev/articles/native-light-dark/) the original cited.

The defensible reasons to keep custom properties primary are:

1. The remaining support gap yields **broken colours, not graceful degradation**. (Correction to the
   original: Safari support for `light-dark()` is **17.5**, not 17.4; Chrome/Edge 123 and Firefox 120
   are correct.)
2. **Chroma palettes are generated stylesheets with literal colour values** that need `[data-theme]`
   scoping regardless. `light-dark()` saves nothing where most of the colour actually lives.

**Behaviour contracts the original omitted:**

- Wrap all `localStorage` access in `try/catch`; define behaviour when storage is unavailable.
- When mode is `auto`, respond to live system theme changes.
- Define and version the storage key.
- Provide a CSS default that is correct before JS executes.
- **CSP:** the inline bootstrap breaks under a nonce/hash CSP unless documented. Publish the script's
  hash per release, or support a `params.cspNonce`.

---

## ADR-5 — Vanilla JS, no framework, fully degradable

**Decision.** No framework. JS is split by page role, not shipped as one bundle.

The original claimed "only three behaviors need JS" while also specifying wrap toggles, tabs, search
and overflow detection. The corrected split:

| Chunk | Contains | Budget |
|---|---|---|
| Inline head guard | `data-theme` stamp before first paint | ~200 B |
| Core article JS (deferred) | theme toggle, copy, wrap toggle, overflow detection, optional TOC scroll-spy | ≤ 3 KB gz |
| Search chunk (lazy, `/search/` only) | search UI and index fetch | ≤ 3 KB gz |
| Tabs | prefer native `<details>` / CSS; JS only if unavoidable | — |

That is **2 script tags on an article page**, down from 11.

**"Fully degradable" made concrete:**

- Tabs expose **all** panels without JS.
- Search shows a clear unavailable state or an HTML browse alternative.
- Copy and wrap controls disappear without hiding or breaking code.
- TOC anchors remain usable without scroll-spy.

---

## ADR-6 — Self-host fonts, but split privacy from performance

**Decision.** Self-host. Subset WOFF2, `font-display: swap`.

**Rationale correction.** Self-hosting removes a render-blocking third party and the GDPR exposure of
`fonts.googleapis.com`. It is **not automatically faster** than a system stack — it adds transfer
bytes and can cause layout shift. Issue #1 conflated the two.

Therefore: the system monospace stack is the zero-byte fallback and remains fully supported; the
bundled font is opt-out-able and separately budgeted; and the subset must cover box-drawing glyphs
(see [003](003-design-spec.md) REQ-FONT-1). Document licence, subset source, glyph coverage, preload
strategy and `font-display` behaviour.

---

## ADR-7 — No required images

**Decision.** Cover images are an optional capability, never a layout assumption.

The best-supported decision in the document, and its premise strengthened on re-measurement: zero
Markdown body images, and `image:` front matter on **1 post of 497 (0.2%)** — not the 6 (1.2%) the
original claimed, which was a non-fence-aware grep hit on `image:` keys inside Kubernetes YAML.

OG image fallback is defined independently of layout.

---

## ADR-8 — Documented extension points, not template forking

**Decision.** Runbook ships stable, empty, documented override partials:

`custom-head.html` · `custom-body-start.html` · `custom-body-end.html` · `comments.html` ·
`article-footer.html` · `custom-schema.html`

**Context.** This was absent from issue #1 and is the single biggest adoption gap it had. The
reference deployment is the proof of need: citizix currently carries **10 local override files**
(`_default/baseof.html`, `home.html`, `shortcodes/admonition.html`,
`partials/head/{custom,schema,script}.html`, `partials/google-tag-manager-body.html`,
`_partials/helper/external.html`, `_partials/article/components/photoswipe.html`, `sitemap.xml`).

Without documented hooks, citizix ports Stack's override sprawl wholesale and every theme update
becomes a merge conflict — and every third-party adopter hits the same wall. Analytics, ads and
comments must be injectable **without editing a theme template and without live IDs in the theme**.

---

## ADR-9 — Distribution

**Decision.** Publish Hugo Module metadata (root `hugo.toml` with `[module.hugoVersion]`, tagged
semver releases), but document **git submodule and release archive as the primary install path**.

**Caveat that must be stated.** Hugo Modules require the **Go toolchain** on the consumer's machine —
the same class of external dependency ADR-1 rejects Node for. Offering the module path is nearly
free and it is required by the showcase anyway ([009](009-showcase-compliance.md)), but it should not
be the headline instruction.

---

## Resolved open questions

### Q1 — `sh` vs `bash` normalisation → **non-question, closed**

Chroma's Bash lexer already declares aliases `bash, sh, ksh, zsh, shell` (verified in
`chroma/lexers/embedded/bash.xml`; Hugo documents the same set in its
[syntax highlighting language list](https://gohugo.io/content-management/syntax-highlighting/#languages)).
All 7,143 shell-family blocks already hit the same lexer.

The only work is cosmetic: a display-label map in the render hook (`sh` → `Shell`). No content
changes, no config, no normalisation. Preserve the author-facing language label.

### Q2 — prompt stripping → **premise was false; answer inverts**

Issue #1 assumed "the citizix corpus mostly omits prompts". **Measured: 1,389 lines begin with `$ `
across 318 posts — 64% of the archive** — plus root-`#` prompt blocks. Mixed command-and-output
blocks are routine, so a naive copy button routinely copies output along with the command.

**Decision.** Exact copy remains the default; silent stripping is worse than faithful copying when
the heuristic guesses wrong. Support an explicit per-block opt-in with `console`-lexer semantics:

````
```console {prompt="$"}
$ systemctl status redis
● redis.service - Redis persistent key-value database
```
````

Copy then yields only the prompt lines, prompt stripped. Never infer this from block content.

The original's "config flag, default off" conclusion survives, but its rationale flips from "prompts
are rare here" to **"prompts are common, which is exactly why stripping must be explicit"**. A future
citizix content pass converting mixed blocks to `console` is the durable fix.

### Q3 — command-output treatment → **yes, and the case strengthened**

`wp-block-preformatted` is now 0, which appears to weaken the question. The opposite is true:
**`text` fences grew from 119 to 426** because PR #60 converted raw output `<pre>` blocks into `text`
fences.

**Decision.** Ship a muted, unhighlighted "output" treatment — optional "Output" tag, no primary copy
button, `<samp>`-style presentation — triggered **explicitly** via an `output` language alias or
`{output=true}` attribute.

**Do not** auto-style all `text` or no-language blocks as output; some are configuration files. Note
the interaction with `guessSyntax: true` (which citizix sets): with guessing on, untagged output
receives speculative token colours, which is precisely what this treatment exists to avoid.

### Q4 — font subset coverage → **the risk is box drawing, not exotic languages**

The 47 languages are all ASCII; language count does not determine glyph needs. The real inventory
problem is captured terminal output. See [003](003-design-spec.md) REQ-FONT-1 for the required
Unicode ranges and the 221-post evidence.

Method correction: audit **code points in the corpus**, not lexer names. Retain a fallback monospace
stack, test missing-glyph rendering, and add the resulting WOFF2 transfer to the budgets.

### Q5 — comments → **ship zero providers, ship one hook**

An empty `_partials/comments.html` override point plus documented giscus **and Disqus** snippets.
Nothing loads until the site opts in, keeping theme JS at zero.

**Why not giscus-only, as issue #1 proposed:** citizix runs Disqus (`disqusShortname: citizix`) with
years of existing threads. A giscus-only theme means the reference deployment cannot migrate without
either losing its comment history or hacking the theme — which would invalidate the theme's own
migration story.

### Q6 — Hugo Module path → **yes, offered; not the headline**

See ADR-9.

---

## Decisions still open

These are genuinely undecided and must be closed before the milestone that depends on them.

| # | Question | Needed by |
|---|---|---|
| 1 | Accent hue and the two palette definitions | M1 |
| 2 | Is the bundled font on or off by default? | M1 |
| 3 | Scroll-spy: does its JS cost fit the 3 KB core budget alongside copy, wrap and overflow detection? | M4a |
| 4 | Taxonomy browse strategy for 159 single-use tags — hide, group under "rare", or paginate? | M4a |
| 5 | Search index fields — title + summary + tags only, or include headings? | M4b |
| 6 | Theme config namespace and feature-flag names | M1 |
