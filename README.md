# Runbook

> *A Hugo theme for people who ship procedures, not photographs.*

**Runbook** is a minimal, code-first Hugo theme for technical blogs — sites where the payload is
commands and configuration, not photography. It is MIT-licensed, has no build toolchain, and treats
the **code block as the primary design object** rather than as a styled afterthought.

No Node. No npm. No Tailwind. No framework. Two `<script>` tags on an article page, one of which is
a ~160-byte inline theme guard.

**All URLs in this file are absolute on purpose** — the Hugo Themes showcase copies this README onto
`themes.gohugo.io`, where a relative link resolves against the wrong origin and 404s.

---

## Who it is for

You write posts that are mostly terminal. Your readers copy from them. A theme that centres a hero
image and reserves 400 px of vertical space for a photograph you do not have is working against you.

Every design decision in Runbook was measured against a real 497-post Linux/DevOps archive
([citizix.com](https://citizix.com), the reference deployment) rather than guessed:

| Measured | Value |
|---|---|
| Fenced code blocks | **9,046** across 497 posts — **18.2 per post** |
| Shell family (`sh`, `bash`, `zsh`, `console`) | **79%** of blocks |
| Blocks that are exactly one line | **45.2%** (57.0% are two lines or fewer) |
| Blocks containing a line over 80 characters | **17.5%** — longest single line is **854** |
| Posts drawing box-drawing glyphs (`└ ├ ─ ●`) | **221 posts, 44%**, over 1,177 lines |
| Markdown body images | **0** |
| Posts with a cover image in front matter | **1 of 497** |

Those numbers are the theme's whole argument, and they are reproducible: the profiler that produced
them is committed at
[`scripts/profile_corpus.py`](https://github.com/etowett/hugo-theme-runbook/blob/main/scripts/profile_corpus.py)
and the full profile — with method, caveats and what changed on re-measurement — is
[specs/002](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/002-corpus-profile.md).

## What that buys you

- **Chrome that scales with content.** No header bar unless `file=` or `caption=` gives it something
  to say. At 18.2 blocks per post, a bar-by-default is chrome taller than its own content on the
  majority of blocks, and it flickers on and off down the page.
- **Horizontal scroll, never soft wrap by default.** Wrapping a `kubeadm join` silently changes what
  the reader believes the command to be. A wrap toggle appears only on blocks that actually overflow.
- **A copy button that works on touch and by keyboard,** with an opt-in `{prompt="$"}` mode that
  copies the commands out of a mixed command-and-output block and leaves the output behind.
- **`tabindex` applied by measurement, not by markup.** Chroma emits `<pre tabindex="0">`
  unconditionally; Runbook strips it and re-adds it only to blocks that really scroll.
- **Line numbers cannot be turned on site-wide by accident.** `markup.highlight.lineNos` in a
  consuming site's config has no effect on Runbook's blocks — the render hook builds its own option
  set from scratch, and CI asserts the build is byte-identical with those settings forced on.
- **A syntax palette that was solved, not picked.** 156 contrast assertions across both themes,
  every Chroma token against every background that can slide underneath it, plus deuteranopia and
  protanopia simulation so colour survives as a *signal*. See
  [docs/accessibility.md](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/accessibility.md).
- **Text-first list views** that never reserve space for a cover image that does not exist.

## Requirements

| | |
|---|---|
| Hugo | **v0.146.0 or later**. Extended is **not** required |
| Toolchain | none — no Node, no npm, no Go (unless you choose the Hugo Modules install path) |

Runbook targets Hugo's post-v0.146.0 template system (`layouts/_markup/`, `layouts/_partials/`,
`page.html`, `home.html`) and ships no legacy layout tree, which is why the floor is a hard one
rather than a suggestion —
[ADR-0](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md).

### One setting your site must have

```toml
[markup.highlight]
  noClasses = false
```

Runbook ships **class-based** Chroma with light and dark palettes scoped under `[data-theme]`
([ADR-2](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md)).
`noClasses = true` writes inline colours into every token and makes dual-theme highlighting
impossible without emitting every block twice. This is the one consuming-site setting Runbook cannot
work around.

Everything else has a default. The full annotated reference is
[docs/configuration.md](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/configuration.md).

---

## Install

### Git submodule — recommended

```bash
cd your-site
git submodule add https://github.com/etowett/hugo-theme-runbook.git themes/hugo-theme-runbook
git submodule update --init --recursive
```

```toml
# hugo.toml
theme = "hugo-theme-runbook"

[markup.highlight]
  noClasses = false
```

Update later with `git submodule update --remote themes/hugo-theme-runbook`, and pin to a tag with
`git -C themes/hugo-theme-runbook checkout v1.2.3`.

### Release archive — no submodule, no extra tooling

```bash
cd your-site
mkdir -p themes
curl -sSL https://github.com/etowett/hugo-theme-runbook/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=1 -C themes/hugo-theme-runbook
```

Tagged archives live on the
[releases page](https://github.com/etowett/hugo-theme-runbook/releases) — prefer a tag over `main`
once one exists. **There is no tagged release yet**; see
[CHANGELOG.md](https://github.com/etowett/hugo-theme-runbook/blob/main/CHANGELOG.md).

### Hugo Modules — offered, but not the headline

```bash
hugo mod init github.com/you/your-site
```

```toml
[module]
  [[module.imports]]
    path = "github.com/etowett/hugo-theme-runbook"
```

This works and the module metadata is maintained, but **Hugo Modules require the Go toolchain
installed on every machine that builds the site**, including your CI runner and anyone who clones
your repository. That is the same class of external dependency Runbook rejects Node for, so it is
offered second on purpose —
[ADR-9](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/006-architecture-decisions.md).
If you already run `hugo mod`, use it. If you do not, the submodule path costs you nothing.

---

## Demo

The showcase demo is the
[`exampleSite/`](https://github.com/etowett/hugo-theme-runbook/tree/main/exampleSite) in this
repository — never the reference deployment, which carries third-party tracking the showcase rules
exclude
([specs/009 §3](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/009-showcase-compliance.md)).

**It is not deployed yet.** `theme.toml` declares
`https://hugo-theme-runbook.netlify.app/` as the demo URL and that host currently returns 404;
standing it up is an M6 task
([specs/008](https://github.com/etowett/hugo-theme-runbook/blob/main/specs/008-milestones.md)). Until
then, run it yourself:

```bash
git clone https://github.com/etowett/hugo-theme-runbook.git
cd hugo-theme-runbook
hugo server --source exampleSite \
            --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
            --disableFastRender
```

`--themesDir <parent> --theme <basename>` rather than `--themesDir ../..` is deliberate and it
matters — see
[CONTRIBUTING.md](https://github.com/etowett/hugo-theme-runbook/blob/main/CONTRIBUTING.md).

---

## Documentation

| | |
|---|---|
| [Configuration reference](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/configuration.md) | Every `params.runbook.*` key, the front-matter schema, override precedence, CSP |
| [Code blocks](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/code-blocks.md) | Attributes, prompt copy, output blocks, line numbers, overflow |
| [Design tokens](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/design-tokens.md) | The `--rb-*` custom properties, both palettes, the bundled font |
| [Extending without forking](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/extending.md) | The six override hooks, with giscus and Disqus snippets |
| [Accessibility statement](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/accessibility.md) | Conformance target, what was tested, and what was not |
| [Verification](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/verification.md) | Every gate, how to run it locally, and what is still a placeholder |
| [Contributing](https://github.com/etowett/hugo-theme-runbook/blob/main/CONTRIBUTING.md) | Build commands, gates, file ownership, golden updates |
| [Security policy](https://github.com/etowett/hugo-theme-runbook/blob/main/SECURITY.md) | How to report, and the surfaces that actually matter |
| [Changelog and version policy](https://github.com/etowett/hugo-theme-runbook/blob/main/CHANGELOG.md) | Semver scope, deprecation windows, latest-Hugo breakage SLO |
| [Specifications](https://github.com/etowett/hugo-theme-runbook/tree/main/specs) | Why every decision was made, with the measurements behind it |

Documentation for search, shortcodes and migrating an existing site is landing as those milestones
merge — see the
[open issues](https://github.com/etowett/hugo-theme-runbook/issues).

## Status

**Pre-release.** M0–M4a are merged: the design system, the code block, templates, SEO, taxonomy,
navigation, the verification harness and CI. Search, shortcodes, the citizix migration guide and the
release polish are in flight. There is no tagged version yet, so treat `main` as moving.

---

## Licences

The theme is [MIT](https://github.com/etowett/hugo-theme-runbook/blob/main/LICENSE). Everything
bundled with it, in full:

| Component | Licence | Notes |
|---|---|---|
| Theme source — layouts, CSS, JS, scripts, docs, specs | **MIT** | © 2026 Eutychus Towett |
| `static/fonts/jetbrains-mono-subset.woff2` | **OFL-1.1** | JetBrains Mono v2.304, © 2020 The JetBrains Mono Project Authors. Licence text shipped at [`static/fonts/OFL.txt`](https://github.com/etowett/hugo-theme-runbook/blob/main/static/fonts/OFL.txt) |
| Icons (copy, copied, wrap, external-link) | **MIT** | Original, hand-authored SVG path data, inlined as `mask-image` data URIs in [`assets/css/code.css`](https://github.com/etowett/hugo-theme-runbook/blob/main/assets/css/code.css). No icon font, no icon library, no third-party request |
| `exampleSite/` content | **MIT** | Written for this repository. The two large fixtures are **generated** by [`scripts/check_fixtures.py`](https://github.com/etowett/hugo-theme-runbook/blob/main/scripts/check_fixtures.py), not copied from upstream projects |
| `images/screenshot.*`, `images/tn.*` | — | **Not present yet.** They will be MIT, captured from `exampleSite` once the demo is deployed (M6) |

**On the font name.** JetBrains Mono is OFL-1.1 with **no Reserved Font Name**. That is what makes a
464-glyph subset legal to ship *under the name JetBrains Mono*; with an RFN it would have to be
renamed. The subset was cut with `pyftsubset` and the exact command is recorded in
[docs/design-tokens.md §4](https://github.com/etowett/hugo-theme-runbook/blob/main/docs/design-tokens.md),
so it is reproducible rather than a binary of unknown provenance.

The bundled font is a **capability, not a requirement**: `params.runbook.bundledCodeFont = false`
falls back to the zero-byte system monospace stack and no font is downloaded at all.

## Acknowledgements

Hugo, and [Chroma](https://github.com/alecthomas/chroma), which does the syntax highlighting Runbook
spends most of its effort colouring correctly.
