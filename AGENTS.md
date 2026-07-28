# AGENTS.md

Instructions for coding agents working on **Runbook**. Written to the
[AGENTS.md](https://agents.md/) convention — a Linux Foundation-stewarded format that Codex,
Cursor, Copilot, Jules, Aider and Zed read directly. Claude Code reads `CLAUDE.md`, which is a
two-line file importing this one, so there is a single source of truth and nothing to keep in
sync.

> **Humans:** you want [CONTRIBUTING.md](CONTRIBUTING.md). This file is the subset of it that an
> agent gets wrong, plus the pointers it needs to find the rest. Everything here is derived from
> [`docs/contracts.md`](docs/contracts.md), [`specs/`](specs/) and the CI workflows; where they
> disagree with this file, **they win** and this file is the bug.

---

## What this repository is

A Hugo theme for technical blogs, where the code block is the primary design object rather than a
styled afterthought. Every design decision was measured against a real 497-post archive
([`specs/002`](specs/002-corpus-profile.md)) rather than guessed.

**There is no build toolchain and adding one is a design decision, not a convenience**
([ADR-1](specs/006-architecture-decisions.md)). No Node, no npm, no bundler, no `pip install`.
Hugo assembles the CSS and JS through its own pipeline; every gate is `python3` and the standard
library. If you find yourself reaching for a package manager, you have misread the problem.

| | |
|---|---|
| Hugo | ≥ **0.146.0**, extended **not** required. Develop against latest; CI builds both ends |
| Python | 3.8+ for most gates; `check_showcase.py` needs 3.11+ for `tomllib` |
| Everything else | nothing. `npx playwright` only for the visual suite, which is not wired into CI |

---

## Orientation — read before editing

Do not start from the file you were asked to change. Start here:

1. [`docs/contracts.md`](docs/contracts.md) — **who owns which file**, the frozen shared names, and
   §3, the list of Hugo behaviours that were measured rather than assumed. §0 supersedes §1.
2. [`specs/README.md`](specs/README.md) — the six decisions that shaped everything, each with the
   measurement behind it.
3. [`docs/verification.md`](docs/verification.md) — every gate, why it exists, and which numbers in
   it are still placeholders.
4. The doc for the area you are touching:
   [code blocks](docs/code-blocks.md) · [design tokens](docs/design-tokens.md) ·
   [configuration](docs/configuration.md) · [extending](docs/extending.md) ·
   [search](docs/search.md) · [shortcodes](docs/shortcodes.md) ·
   [accessibility](docs/accessibility.md) · [migration](docs/migration.md)

Nothing in this repository is arbitrary. Before "simplifying" something that looks redundant —
the `isset` dance in `utils/settings.html`, the explicit option set in `render-codeblock.html`,
`--themesDir "$(dirname "$PWD")"` — find the comment that says why. There always is one, and it
usually names the bug that produced it.

---

## Build and verify

Run this before you claim anything works. It is a build and seven gates, about fifteen seconds on
a warm checkout, so there is no reason to skip it and guess.

```bash
# 1 — build the demo site exactly as CI does
hugo --source exampleSite \
     --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination "$PWD/public" --cleanDestinationDir --gc --minify \
     --panicOnWarning --printPathWarnings

# 2 — the gates that run on every pull request
python3 scripts/check_reqcb1.py                    # builds twice itself and diffs
python3 scripts/check_fixtures.py --check-generated
python3 scripts/check_jsonld.py   public --require-article
python3 scripts/check_budgets.py  public
python3 scripts/check_links.py    public           # internal only
python3 scripts/check_contrast.py                  # -v for all 150 ratios
python3 scripts/check_showcase.py                  # advisory until M5
```

Claude Code users: **`/gates`** runs all of the above and reports each result.

**Two spellings that are not style preferences.**

- **`--themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")"`, never `--themesDir ../..`.**
  `exampleSite/hugo.toml` declares `theme = "hugo-theme-runbook"`, so Hugo looks for a *directory
  of that name* inside `--themesDir`. `../..` resolves only because a default checkout happens to
  sit in a directory with the repository's name. In a **git worktree**, a renamed clone or a
  renamed fork it fails with `module "hugo-theme-runbook" not found` — reproduced 2026-07-28.
  `.claude/hooks/guardrails.py` blocks the `../..` spelling for that reason.
- **`--panicOnWarning` is mandatory.** Hugo logs genuinely broken things — a missing layout, a
  shortcode called with the wrong arguments, a deprecated function — at WARN and then exits 0.
  Without it, a build that renders nothing useful is a green tick.

And one that is not written down anywhere else: **`--destination` must be absolute.** Hugo
resolves a relative `--destination` against `--source`, so `--source exampleSite --destination
public` writes to `exampleSite/public/` and every gate then fails with `public is not a
directory`. CI avoids it by passing `$RUNNER_TEMP/public`; the local recipe in
[CONTRIBUTING.md](CONTRIBUTING.md#running-the-gates) still has the relative form —
`TODO(release-hygiene): fix, it is that stream's file`.

Reproducing the CI floor locally, which catches template features that only exist after 0.146.0:

```bash
RB_HUGO=/path/to/hugo-0.146.0 python3 scripts/check_reqcb1.py     # or: /gates floor
```

**Do not try to run the parity job.** `.github/workflows/parity.yml` builds a **private** reference
archive and is `workflow_dispatch`/`schedule` only, deliberately. It cannot run from a fork or a PR.

---

## The traps

These are the failure modes that cost real time here. Each is silent — the build stays green and
the output is wrong.

### 1 — Never add `layouts/_default/`

Runbook targets Hugo's post-v0.146.0 template system only: `layouts/_partials/`, `layouts/_markup/`,
`page.html`, `home.html`. **When a legacy `layouts/_default/` path exists alongside the new one, the
legacy one wins, silently** ([ADR-0](specs/006-architecture-decisions.md)). The guardrail hook
blocks writes to that path.

### 2 — A boolean that defaults to `true` is resolved with `isset`, never `| default true`

`false | default true` evaluates to `true`, so the obvious spelling silently ignores every consumer
who turns the feature off. `isset` distinguishes "absent" from "present and false". Hugo lower-cases
every param key and `isset` is case-sensitive, so the probe string is lower-case:

```go-html-template
{{- $showLastmod := true -}}{{ if isset $rb "showlastmod" }}{{ $showLastmod = $rb.showLastmod }}{{ end }}
```

Follow the pattern already in [`layouts/_partials/utils/settings.html`](layouts/_partials/utils/settings.html).

### 3 — Configuration is namespaced, defaulted twice, and documented in the same PR

Namespace is **`params.runbook.*`** ([contracts §2.4](docs/contracts.md)). Nothing is read from a
bare top-level param, ever, so Runbook cannot collide with a consumer's keys. A new setting needs
**all four** of these or it is not done:

1. a default in the root `hugo.toml`,
2. an inline default in `_partials/utils/settings.html` (see trap 2 for booleans),
3. every user-visible string it introduces added to `i18n/en.yaml`, **inside your own section**,
4. an entry in `docs/configuration.md` — or, if that file is not yours, a line in the PR body so
   its owner can fold it in.

A setting that exists only in a template is a setting nobody can discover. `/new-setting` walks
this.

### 4 — The code-block render hook must not trust site config

`transform.Highlight` applies the *consuming site's* `markup.highlight` defaults for any key the
caller leaves unset, and Hugo merges theme config underneath site config, so a theme default cannot
fix it. **The hook passes `lineNos` and `lineNumbersInTable` on every call, not only when true** —
an unset key is where the consumer's config gets back in. `check_reqcb1.py` proves the build is
byte-identical with those settings forced on; it runs on every PR and it is the strictest thing in
CI. Two more measured facts live in [contracts §3](docs/contracts.md): Chroma emits
`<pre tabindex="0">` unconditionally and the hook must strip it, and highlighted lines are
`<span class="line hl">` so a bare `.hl` selector matches nothing.

### 5 — Deprecations cut both ways across the supported range

Hugo v0.158.0 deprecated `languageCode`, `.Language.LanguageCode` and `.Language.LanguageDirection`.
Their replacements **do not exist at the 0.146.0 floor**, so either side of that pair breaks one end
of the CI matrix — and `--panicOnWarning` turns a deprecation warning into a failure. Use
`site.Language.Lang` and a language param for direction, which are stable across the whole range.

### 6 — `gzip -n -9`, always

Without `-n`, gzip writes a modification timestamp into the header, byte counts move between runs
and every budget gate goes flaky. Separately: **compare page weights on one platform only** — GNU
gzip on the Linux runner and Apple gzip on macOS disagree by ~5% on the same build, so a baseline
captured on a laptop reports a regression on CI that is really a difference of implementation.

---

## File ownership

Four workstreams merge in parallel and a cross-boundary edit is a merge conflict.
[`docs/contracts.md`](docs/contracts.md) is the map and **§0 supersedes §1 for work in flight.**

1. **Do not edit a file another workstream owns.** If you need something changed there, say so in
   the PR description and let the owner change it.
2. **Names in the shared contracts are frozen.** Adding is fine; renaming lands in someone else's
   file.
3. `README.md`, `LICENSE`, `theme.toml`, `hugo.toml`, `specs/**` and `docs/contracts.md` belong to
   nobody — changes to those go in **their own PR**.

Shared files with explicit seams, so they do not become conflicts:

| File | Seam |
|---|---|
| `assets/css/components.css`, `search.css` | already in the concat list in `head/css.html`. **Nobody edits that list.** `resources.Get` skips a missing stylesheet, so an empty one is harmless |
| `i18n/en.yaml` | sectioned — append inside **your** section |
| `assets/js/runbook.js` | **frozen** at three modules. Own your module, not the entry point. Search is a separate lazy chunk with its own budget |
| `docs/configuration.md` | belongs to the release-hygiene stream — see trap 3 |

---

## Style

- **Go templates:** `{{-` / `-}}` trimming as in the existing files; `partialCached` for anything
  whose answer cannot vary per page; every user-visible string from `i18n/en.yaml`, no exceptions.
- **CSS:** custom properties are prefixed `--rb-` and declared in `assets/css/tokens.css`. Read that
  file before inventing a token. The load order in `head/css.html` is the cascade contract:
  `tokens → base → layout → code → chroma-light → chroma-dark → print`.
- **JavaScript:** no framework, no bundler, no dependencies. Everything reachable from
  `assets/js/runbook.js` shares **one 3 KB gzipped budget**; `/search/` has its own 3 KB. Guard each
  module in `try`/`catch`.
- **Python:** standard library only, `#!/usr/bin/env python3`, module docstring naming the spec
  section the gate implements. Match the existing scripts.
- **Prose:** British spelling, em dashes, no exclamation marks. Say why, not what.

---

## Testing

- **Add the fixture with the feature, not afterwards.** Synthetic fixtures live in
  `exampleSite/content/` and are what protects a rendering path once the reference archive stops
  exercising it. A shipped template that no fixture reaches fails CI — `check_unused_templates.py`
  allows a fallback only with a written reason in `.github/unused-templates-allowed.txt`, and a
  waiver that goes stale fails too.
- **Measure rather than assert.** Two of the code block's real bugs — `padding-inline-end` not
  counting toward scrollable overflow, and a `<td>` growing so its inner `<pre>` never gets a width
  to scroll against — were invisible in the markup and were found by **driving a browser**. If a
  claim in a PR body is a number, it must be reproducible from a command in that body. `.mcp.json`
  wires up Playwright for exactly this; see [Tooling](#tooling).
- **Visual regression is scaffolded, not enabled,** and no baselines are committed on purpose until
  the visual freeze. Do not generate goldens. The golden-update workflow is in
  [CONTRIBUTING.md](CONTRIBUTING.md#visual-regression-and-the-golden-update-workflow).

---

## Git and pull requests

- **Never commit to `main`.** Branch as `eutychus/<short-slug>`, matching the existing history.
- One workstream per PR, matching the ownership map.
- **Say why, not what.** The diff already says what; the body carries the reasoning, the
  measurements, and anything you tried that did not work.
- Include gate results — budgets in gzipped bytes, contrast assertion count, `--panicOnWarning`
  clean.
- **Name any cross-boundary change you need rather than making it.**
- Update the documentation in the same PR. A follow-up documentation commit does not happen.
- **If a claim cannot be verified from the files, write `TODO(name): confirm …` rather than
  guessing.** This is the single most important rule in the repository and it applies to agents
  more than to anyone else.
- Do not add `images/screenshot.*` or `images/tn.*` to make `check_showcase.py` pass. They are
  absent on purpose until M6 — see [CONTRIBUTING.md](CONTRIBUTING.md#screenshots-for-the-showcase).

---

## Tooling

Committed under [`.claude/`](.claude/) and [`.mcp.json`](.mcp.json). Claude Code reads all of it
automatically; other agents can read the sources directly.

| | |
|---|---|
| **Skills** | `/gates` build + every PR gate (`/gates floor` for the 0.146.0 end of the matrix) · `/serve` dev server, spelled correctly · `/new-setting` the config ritual in trap 3 · `/code-block` the render-hook contract · `/hugo-templates` the post-0.146 lookup rules and the version-floor traps |
| **Hook** | [`.claude/hooks/guardrails.py`](.claude/hooks/guardrails.py) — a `PreToolUse` guard that blocks the traps above *before* the edit lands rather than minutes later in CI, with an error that names the mistake rather than a gate |
| **Tests** | `python3 .claude/hooks/test_guardrails.py` — 33 cases, half of them "this must **not** fire", including a replay of every tracked file through the hook |
| **MCP** | Playwright ([`.mcp.json`](.mcp.json)), for the "measure rather than assert" rule. Opt-in: Claude Code asks before loading a project-scoped server, and nothing in CI or in the build needs it |

Two notes on the hook. **Every rule cites the spec that makes it a rule** — if you cannot point at
the line that makes something wrong, it does not belong in there. And **a false positive is a bug
in the hook, not something to work around**: fix the rule and add the case to
`test_guardrails.py`. That happened three times while the hook was being written — `hugo build
--help` read as a build; the `--printUnusedTemplates` step, which `ci.yml` deliberately runs
*without* `--panicOnWarning`; and the `gh issue create` heredoc containing the issue that proposed
the hook, blocked because the text quotes the wrong command in order to warn about it. Every doc
and PR body here does that, so a heredoc body is now treated as data rather than as a command. All
three are regression cases in the suite.

`.mcp.json` needs `npx`, which is the one place this repository touches Node. It does not
contradict [ADR-1](specs/006-architecture-decisions.md): ADR-1 is about the **build**, and
CONTRIBUTING.md already sanctions `npx playwright` for the visual suite. Nothing here is required
to build the theme, run a gate, or pass CI.
