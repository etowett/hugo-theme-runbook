# Verification

**Owner:** the fixtures / CI / verification workstream ([contracts §1 D](contracts.md#1-file-ownership)).
**Plan:** [007 — Verification](../specs/007-verification.md), with budgets from
[005](../specs/005-performance-budgets.md) and showcase rules from [009](../specs/009-showcase-compliance.md).

Everything here runs with **python3 and the standard library**. No Node, no npm, no pip install —
[ADR-1](../specs/006-architecture-decisions.md) keeps the theme free of a build toolchain, and a
gate that needs one is a gate contributors skip.

---

## 1. Running it locally

### Pointing Hugo at the checkout

`exampleSite/hugo.toml` declares `theme = "hugo-theme-runbook"`, so Hugo looks for a **directory of
that name** inside `--themesDir`. That single line decides how every command below is written.

On a default GitHub checkout the workspace path already ends in the repository name
(`/home/runner/work/hugo-theme-runbook/hugo-theme-runbook`), so `--themesDir ../..` happens to
resolve. It is worth being clear that this is a coincidence of the runner's layout, not a property
of the repository: it breaks in a git worktree, in a clone with a different directory name, and in a
fork whose repository was renamed. Any of those produce `module "hugo-theme-runbook" not found`.

So every command here pairs `--themesDir <parent>` with `--theme <basename>`:

```bash
# From the repository root. Works in a fresh clone, a renamed clone, and a worktree.
hugo --source exampleSite \
     --themesDir "$(dirname "$PWD")" \
     --theme "$(basename "$PWD")" \
     --destination public \
     --cleanDestinationDir --gc --minify \
     --panicOnWarning --printPathWarnings --printUnusedTemplates
```

The CLI flag beats the config file, so this needs no symlink and no edit to
`exampleSite/hugo.toml`, which is owned by the templates workstream
([contracts §1 C](contracts.md#1-file-ownership)). `.github/workflows/ci.yml` derives the same two
values from `$GITHUB_WORKSPACE`.

Dev server:

```bash
hugo server --source exampleSite --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
            --disableFastRender
```

### The gates

```bash
python3 scripts/check_reqcb1.py                  # builds twice itself
python3 scripts/check_fixtures.py --check-generated
python3 scripts/check_jsonld.py   public
python3 scripts/check_budgets.py  public
python3 scripts/check_links.py    public         # internal only; add --external for the sweep
python3 scripts/check_showcase.py                # advisory; add --network to resolve the demo URL
python3 scripts/check_contrast.py                # owned by the design workstream
python3 scripts/check_agents.py                  # the tooling, not the theme — see below
```

Reproducing the CI matrix locally against the 0.146.0 floor:

```bash
RB_HUGO=/path/to/hugo-0.146.0 python3 scripts/check_reqcb1.py
```

### Reproducibility

`gzip -n -9` throughout. **The `-n` is mandatory** — without it gzip writes a modification timestamp
into the header, byte counts move between runs, and every budget gate goes flaky. A budget check
that omits it is not reproducible. `scripts/check_budgets.py` shells out to the real `gzip` binary
rather than using zlib, so its numbers match the command quoted in
[005 §5](../specs/005-performance-budgets.md#5-reproducibility) by hand.

**Compare page weights on one platform only.** Measured on the same build, GNU gzip on the Linux
runner and Apple gzip on macOS disagree: the article p50 reads 2,585 B on CI and 2,728 B locally.
The theme-shell figures happen to agree exactly (CSS 2,125 B, JS 481 B), but that is luck, not a
property. So the p50/p90 gates and any `--baseline` file must be produced and consumed on the same
platform — a baseline captured on a laptop and compared on a runner reports a regression that is
really a difference of gzip implementation.

---

## 2. What CI runs

### `.github/workflows/ci.yml` — every push and pull request

| Job | Blocking | What it does |
|---|---|---|
| **Build** (matrix) | yes | Builds `exampleSite` on **Hugo 0.146.0 non-extended** and **latest extended**, with `--panicOnWarning --printPathWarnings --printUnusedTemplates`, then runs the REQ-CB-1, fixture, JSON-LD and budget gates on each |
| **Contrast** | yes, once it exists | Runs `scripts/check_contrast.py`; emits a notice and passes while the file is absent (design workstream, [contracts §1 A](contracts.md#1-file-ownership)) |
| **Agent config** | yes | `scripts/check_agents.py` and `test_guardrails.py`. The mirror gate — see §2.1 |
| **Showcase** | no (`continue-on-error`) | `scripts/check_showcase.py`. Advisory until M5 — see §5 |

#### 2.1 Why the agent-config job runs on the runner and not only locally

Everything `check_agents.py` asserts can be checked on a laptop except one thing, and that one thing
is why the job exists: **a path whose case is wrong resolves on macOS and fails on Linux.** The
defect that produced this gate was a copied skill file reading `.Codex/hooks/` where the directory
is `.codex/`. It worked on the machine that wrote it, worked in every local test, and would have
failed for the next contributor. The case-sensitivity check compares every `.<dir>/` reference in
the tooling against the real directory names, so it catches the mistake on either platform — but the
runner is the platform where the underlying bug actually bites.

The job also fails on a machine-specific absolute path in shared config, a mirror that disagrees
with its canonical source (including MCP server *arguments*, which is where a version pin lives), a
skill description over its context budget, a subagent granted write tools, and a number quoted in
prose that the gate it describes no longer reports. That last one is not hypothetical: the contrast
gate moved from 150 to 156 assertions and five files kept saying 150.

Both matrix legs matter and can break independently. The minimum is what `theme.toml` and
`[module.hugoVersion]` promise, and it is built **non-extended** because ADR-0 declares extended is
not required — a theme that quietly needs extended has broken its own manifest. Latest is what the
Hugo Themes showcase builds with.

`--panicOnWarning` is not optional. Hugo logs genuinely broken things — a missing layout, a
shortcode called with the wrong arguments, a deprecated function — at WARN level and then exits 0,
so without it a build that renders nothing useful is a green tick.

[contracts §3](contracts.md#deprecations-vs-the-version-floor) records the specific hazard that
makes the matrix necessary: v0.158.0 deprecated `languageCode`, `.Language.LanguageCode` and
`.Language.LanguageDirection`, whose replacements do not exist at the 0.146.0 floor. Either side of
that pair breaks one end of the matrix, and `--panicOnWarning` turns the deprecation into a failure
rather than a line that scrolls past.

The build job also runs a **hostile-configuration step**: the site is rebuilt with `noClasses=true`,
`guessSyntax=true`, `unsafe=true` and all of them at once, forced through `HUGO_*` environment
variables. Unlike REQ-CB-1 these legitimately change the output, so the assertion is only that the
build still succeeds — but a theme distributed to strangers is built against configuration it did
not choose, and "it builds on my config" is not the claim being made.

### `.github/workflows/scheduled.yml`

| Trigger | Job | Why it is not on a PR |
|---|---|---|
| `0 22 * * *` daily | Build against **latest** Hugo | It can break with no change to this repository. The showcase rebuilds every theme daily at 00:00 UTC and a theme that stops building disappears from it with no notice ([009 §4](../specs/009-showcase-compliance.md)). 22:00 UTC is deliberate: two hours before the showcase rebuild, so CI finds it first |
| `0 3 * * 1` weekly | **External link sweep** | It takes minutes over thousands of links, hits rate limits, and fails when a third party's docs site is down. Gating a PR on that produces a red X nobody can act on, which teaches people to ignore CI ([007 §3.5](../specs/007-verification.md)) |
| daily, with the build | **Demo site resolves** — `check_showcase.py --network` | It fetches `theme.toml`'s `demosite` URL, and a pull request must not go red because a host is down. It is also drift nothing else can see: the showcase links a visitor straight at that URL ([009 §2](../specs/009-showcase-compliance.md)) while every build stays green. `demosite` sat at a URL that had never once resolved, and the one check that mentioned it deferred to a verification nothing performed (issue #46) |

All three open or update a **tracking issue** on failure rather than only turning a square red,
because a scheduled job nobody is watching fails silently.

`netlify.toml` is what the demo job exists to guard: it builds `exampleSite` with the
`--themesDir <parent> --theme <basename>` spelling, because Netlify checks the repository out into
a directory named `repo` and `--themesDir ../..` fails there exactly as it does in a worktree. It
overrides `--baseURL` at deploy time from Netlify's own `$URL`/`$DEPLOY_PRIME_URL` so the committed
`baseURL = "https://example.com/"` — which [009 §2](../specs/009-showcase-compliance.md) requires
and `check_showcase.py` asserts — stays hermetic. **The Netlify site itself still has to be created
and connected to the repository**, which is why `theme.toml` carries no `demosite` value yet.

#### The link exclusion list

`.github/link-exclusions.json` is `{regex: reason}` and **the reason is structurally mandatory** —
`scripts/check_links.py` fails on an entry whose reason is empty. Two things that mattered in
practice on the reference site:

- Some hosts answer 403 or 418 to any automated checker while working perfectly in a browser.
  Without a recorded reason, the next person tidying the list deletes a real exclusion.
- **Exclude only false positives.** A genuinely dead link gets fixed. The reference site's link
  check excluded *every* absolute URL, so no outbound link had ever been verified and 12 dead ones
  accumulated — two pointing at repositories that no longer existed, one at a page that never had.

---

## 3. The REQ-CB-1 gate

`scripts/check_reqcb1.py` builds `exampleSite` twice, the second time with the reference site's own
hostile settings forced through the environment:

```bash
HUGO_MARKUP_HIGHLIGHT_LINENOS=true HUGO_MARKUP_HIGHLIGHT_LINENUMBERSINTABLE=true
```

The two trees must be **byte-identical**, fingerprinted asset names included.

This is a better test than "assert zero `<table class=lntable>` in the archive build" on two counts.
It needs no pinned reference content, so it runs on every PR in a few seconds. And it is strictly
stronger: a `lntable` grep catches only the one symptom already known about, whereas an identity
diff catches *any* structural leak of consumer configuration into theme output — a future
`markup.highlight` key that changes emitted structure rather than emitted colour is caught the day
it is forwarded, with no new test written.

Both builds run with `--gc --minify`, so the comparison is over the markup that actually ships.

Verified failing correctly: with the render hook changed to pass fence options straight through to
`transform.Highlight`, the gate reports six differing files and prints the `lntable` markup appearing
in the hostile build.

---

## 4. Budgets, and the script-tag decision

### The script-tag budget counts EXECUTABLE scripts only

[005 §3.1](../specs/005-performance-budgets.md#31-theme-shell-budgets--hard-ci-gates) budgets
**≤ 2 `<script>` tags per article**. The current build emits three:

1. the inline theme guard in `head/theme-guard.html`,
2. `<script defer src="/js/runbook.…js">`, the one bundle,
3. `<script type="application/ld+json">`, the structured data block.

**Decision: the budget counts executable scripts. The real count is 2 and the budget is met.**

The budget exists to bound parse and execute cost and main-thread blocking. An `ld+json` block is a
data island: the HTML specification classifies it as a data block, the browser never hands it to the
JavaScript engine, it triggers no network request and it blocks nothing. Counting it would force one
of two bad outcomes — drop structured data to satisfy an arithmetic target, or quietly raise the
number to 3 later, at which point the budget no longer means what it said and the next data block
raises it to 4.

Concretely, `scripts/check_budgets.py` counts a `<script>` whose `type` is absent, empty, a
JavaScript MIME type, or `module`. Everything else — `ld+json`, `importmap`, `speculationrules`,
`text/template` — is reported separately and not counted. The rule and its reasoning are in the
`SCRIPT-TAG DECISION` block at the top of that file as well as here, so it cannot be silently
redefined by editing one number.

The budget is enforced on **every** article page, not only on the measurement fixture.

### Theme-shell budgets are hard ceilings

Measured on `exampleSite/content/posts/theme-shell-baseline.md` — a deliberately minimal synthetic
page, named explicitly in the script rather than "whichever article sorts first", so the figure
reflects only what the theme emits.

| Asset | Budget | At this commit |
|---|---:|---:|
| CSS, total | ≤ 8,000 B gz | 2,125 |
| Core article JS | ≤ 3,000 B gz | 481 |
| Search chunk | ≤ 3,000 B gz | not built |
| Bundled code font, per subset | ≤ 30 KB raw | not built |
| Executable `<script>` tags | ≤ 2 | 2 |
| Third-party hosts | 0 | 0 |

The current numbers are small because most of the theme does not exist yet. They are a floor to
regress from, not an achievement.

### Page-weight budgets are PLACEHOLDERS and are not enforced

`scripts/check_budgets.py` measures the p50, p90, maximum and minimum of article page weight, the
homepage, and taxonomy pages, and implements a per-page **no-regression** rule against a recorded
baseline. All of that machinery is complete and tested. **The thresholds are `None`.**

This is deliberate, and copying the numbers out of
[005 §3.2](../specs/005-performance-budgets.md#32-page-weight-budgets--distribution-gates-not-ceilings)
would be wrong. That table sets p50 ≤ 9,000 B and p90 ≤ 14,000 B as improvements on a Stack baseline
of 10,663 B median and 15,488 B p90. Since then the reference site fixed its JSON-LD and turned off
site-wide line numbers, and the same corpus now measures **9,159 B median and 11,626 B p90 — with
Runbook not existing yet**. The p50 gate would be met by doing nothing and the p90 gate is already
met by the theme being replaced. specs/005 §3.1 carries an explicit
**"Re-baseline required before M3"** warning saying exactly this.

To re-derive them:

```bash
# 1. Build the SAME corpus with the theme being compared against, at the commit you will
#    compare from. A baseline captured at a different commit measures the corpus changing,
#    not the theme changing.
python3 scripts/check_budgets.py <stack-build> --write-baseline .github/budgets/stack-baseline.json

# 2. Build the same corpus with Runbook, and diff per page.
python3 scripts/check_budgets.py <runbook-build> --baseline .github/budgets/stack-baseline.json
```

Then set `PLACEHOLDER_PAGE_WEIGHT` in `scripts/check_budgets.py` from the observed distribution and
pass `--enforce-page-weight` in CI. Until the thresholds are real numbers, `--enforce-page-weight`
deliberately **fails** rather than silently passing on `None`.

The no-regression rule is the one that actually protects readers: a theme cannot compress content,
but it must never make a given page heavier than the theme it replaced rendered it. An absolute
ceiling measures the author's writing.

---

## 5. Showcase compliance

`scripts/check_showcase.py` checks [009 §2](../specs/009-showcase-compliance.md) mechanically and
grades findings, because most of the outstanding work cannot be done yet:

- **FAIL** — a real violation of a rule the repository already claims to meet.
- **TODO** — a requirement whose artefact does not exist yet.
- **NOTE** — owned by a different workstream, or by nobody.

At this commit: **0 fail, 3 todo, 1 note, 8 ok**. Two TODOs are `images/screenshot.{png,jpg}`
(≥ 1500×1000, 3:2) and `images/tn.{png,jpg}` (≥ 900×600, 3:2), which cannot be produced before the
theme renders. The script reports them as missing rather than crashing, and reads PNG and JPEG
dimensions from their headers with no imaging library.

The third is the demo site, and it is the one worth reading twice. `theme.toml` advertised
`https://hugo-theme-runbook.netlify.app/` from the first commit; that host has never resolved, and
because the field was only checked for **presence** the gate reported it as fine (issue #46). The
field is now absent — [009 §2](../specs/009-showcase-compliance.md) requires a public demo site but
does not list `demosite` among the theme.toml fields it requires, so an absent field is an honest
report of undone work where a 404 was a false one. `--network` resolves whatever value is there and
**FAILs on a non-2xx**, on a DNS failure and on a timeout; without the flag the run is hermetic and
touches nothing, so per-PR runs never depend on the network.

The job is `continue-on-error: true` and will stay that way until M5. Run
`python3 scripts/check_showcase.py --strict` to make TODOs fail — that is the release gate, and the
missing demo now fails it.

Note the submission process changed and the old checklist is stale: `gohugoio/hugoThemes` is
archived, `reviewTheme.sh` is gone, and submission is now a **pull request** to
`gohugoio/hugoThemesSiteBuilder` adding the theme URL to `themes.txt` in lexicographical order,
gated by the Netlify deploy preview.

---

## 6. The fixture corpus

Layer 1 of [007 §2](../specs/007-verification.md#2-two-layer-fixture-strategy) lives in
`exampleSite/content/posts/`. These are in the theme repository because they **survive content
cleanups in the reference archive, which the original fixture list demonstrably did not** — three of
its seven required pages no longer exist — and because they are what protects third-party robustness
after the reference site stops exercising these cases.

| Fixture | Guards |
|---|---|
| `code-block-smoke-test.md` | The torture page: one/two/three-line blocks, untagged fence, tilde fence, unknown language, `{linenos=true}`, `{file=}`, `{hl_lines=}`, `{prompt="$"}`, `{output=true}`, the 854-character line, `└ ├ ─ ●` shell output, an indented block, inline code |
| `code-blocks-158.md` | Per-block JS and CSS cost at the corpus maximum of 158 blocks (**generated**) |
| `code-block-767-lines.md` | One block of exactly 767 lines, the corpus maximum (**generated**) |
| `theme-shell-baseline.md` | The synthetic minimal page the theme-shell budgets are measured on |
| `tables-and-data.md` | Wide tables, nested lists, task lists, footnotes |
| `admonitions-and-callouts.md` | GitHub alert blockquotes and the plain blockquotes they must not swallow |
| `prose-only-no-code.md` | The no-code case, and a TOC whose first heading arrives late |
| `rtl-bidirectional-text.md` | Bidi: LTR commands and code blocks inside RTL prose |

`scripts/check_fixtures.py` asserts each property is **still true** — 158 blocks is still 158, the
long line is still exactly 854 characters, the no-code post still has no code. A fixture whose
defining property has quietly drifted still builds, still looks fine, and guards nothing.

The two large fixtures are generated by that same script and regeneration is deterministic:

```bash
python3 scripts/check_fixtures.py --regenerate      # rewrite them
python3 scripts/check_fixtures.py --check-generated  # CI: fail if regeneration would change anything
```

### Finding: an unknown lexer produces a different DOM

Verified against a real build while adding the unsupported-language fixture. A **known** language
renders as

```html
<div class="highlight"><pre tabindex="0" class="chroma"><code class="language-sh" data-lang="sh">
  <span class="line"><span class="cl">…</span></span>
```

whereas an **unknown** one (`frobnicate-9000`, and also `conf`, which Chroma has no lexer for)
renders as

```html
<pre tabindex="0"><code class="language-frobnicate-9000" data-lang="frobnicate-9000">…raw text…
```

No `div.highlight`, no `pre.chroma`, no `span.line`, no `span.cl`. **Any CSS or JS selector keyed on
`.chroma`, `.highlight` or `.line` silently misses these blocks**, which is a third-party robustness
problem rather than a curiosity: a consumer using a vendor DSL tag gets a code block with no chrome,
no copy button and no palette. This is precisely why the row exists in
[007 §2](../specs/007-verification.md).

It also decides the language tag on `code-block-767-lines.md`: it is `ini` rather than `conf`,
because tagged `conf` a 767-line block measures the cost of *not* highlighting. `check_fixtures.py`
asserts that.

### Deliberately absent

- **A malformed fence.** [007 §2](../specs/007-verification.md) says explicitly not to preserve one.
  It is a content bug fixed upstream, and malformed source is tested synthetically only where the
  renderer has a defined fallback.
- **Bare `<pre>` via unsafe HTML.** `exampleSite/hugo.toml` sets
  `markup.goldmark.renderer.unsafe = false`, which [007 §3.5](../specs/007-verification.md) requires
  the build to pass with. Raw HTML is therefore dropped and the fixture would silently test nothing.
  The 4-space indented block already exercises the same styling path (bare `pre > code`, no hook,
  REQ-CB-8). A real version needs a second build configuration with `unsafe: true`; the CI
  hostile-config step already builds that way, so the fixture can be added when there is a layout
  to assert against.
- **Clipboard-unavailable context.** REQ-CB-4's fallback triggers on an insecure origin or a denied
  permission. That is browser state, not page content — it belongs to the Playwright suite.
- **A tabs shortcode.** `layouts/shortcodes/` is owned by the templates workstream and is still
  empty. A shortcode call in content is a hard build failure rather than a graceful degradation, so
  the fixture waits for the shortcode.
- **A page-level `dir="rtl"`.** [contracts §3](contracts.md#3-verified-hugo-behaviour) configures RTL
  per language, which means a `[languages.ar]` block in `exampleSite/hugo.toml` — owned by the
  templates workstream. `rtl-bidirectional-text.md` exercises everything that does not need it: bidi
  mixing in prose, and LTR code blocks inside RTL paragraphs, which is where themes that *do*
  support RTL usually break.

---

## 7. Visual regression, and the golden-update workflow

**Scaffolded, not enabled.** `.github/visual/playwright.config.mjs` pins the environment;
`.github/lighthouse/lighthouserc.json` pins the Lighthouse run. Neither is wired into a workflow and
no baselines are committed.

That is a decision, not an omission. Every baseline captured today would be a screenshot of a
foundation stub while three other workstreams change the stylesheet, the code block and the
templates concurrently. A golden set generated against that gets regenerated wholesale on the first
real commit, which teaches everyone that "just re-approve the goldens" is the normal response to a
red diff — and a suite people re-approve reflexively has negative value, because it costs CI minutes
and catches nothing. **Capture the first baselines at the M4 visual freeze.**

Pinned in the config because each of them changes pixels if left to the machine: browser build,
device scale factor, colour scheme, reduced-motion state, timezone, locale, and an explicit diff
threshold (`maxDiffPixelRatio: 0.002`, `threshold: 0.15`) rather than "whatever looked fine".

### The approved-golden update workflow

A screenshot diff has exactly two causes and they need opposite responses, so the workflow makes the
author say which one it is:

1. **Reproduce locally on the same pinned browser.** Never approve from a CI artefact alone — if it
   does not reproduce locally, the diff is environmental and the config is wrong, not the golden.

   ```bash
   npx playwright test --config .github/visual/playwright.config.mjs
   ```

2. **Classify the diff in the PR description.** Either *intended* — the change was the point, name
   the design decision — or *unintended*, in which case it is a bug and the golden does not move.

3. **Regenerate only the affected projects.** Never the whole set: a blanket `--update-snapshots`
   hides a second, unintended regression inside an intended one.

   ```bash
   npx playwright test --config .github/visual/playwright.config.mjs \
     --project desktop-dark --update-snapshots tests/code-block.spec.mjs
   ```

4. **Commit the new goldens in the same PR as the change that caused them**, never in a follow-up.
   A goldens-only commit is unreviewable — the diff is binary and the reason is gone.

5. **Review the images, not the file list.** GitHub renders image diffs; a reviewer approving
   `+3 -3 baselines/…png` has approved nothing.

6. **A golden update needs the same review as code.** If the only justification is "CI was red", the
   answer is no.

Baseline regeneration on a **font change** is a special case: `└ ├ ─ ●` falling back to another font
mid-block is a visual regression that no unit test sees, which is why the `systemctl status` fixture
is in the capture set specifically (REQ-FONT-1).

---

## 8. What is implemented, what is a placeholder

| | State |
|---|---|
| REQ-CB-1 hostile-config identity diff | **implemented**, verified passing and verified failing on an injected regression |
| Hugo matrix, min + latest, `--panicOnWarning` | **implemented**; 0.146.0 non-extended verified locally |
| Hostile consumer-config build permutations | **implemented** |
| Fixture invariants + deterministic regeneration | **implemented** |
| JSON-LD parse + value assertions | **implemented**; the `Article` assertions are **inert** until `head/schema.html` emits Article schema. Pass `--require-article` at that point |
| Theme-shell budgets | **implemented** as hard gates |
| Script-tag budget | **implemented**, counting executable scripts — §4 |
| Page-weight distribution + no-regression | mechanism **implemented**, thresholds are **placeholders**, no baseline committed — §4 |
| Internal link and fragment crawl | **implemented**, runs nightly in `scheduled.yml` and in `parity.yml` — NOT in `ci.yml`, so it is not a per-PR gate |
| External link sweep | **implemented**, weekly, tracking issue on failure |
| Showcase compliance | **implemented**, advisory until the screenshots exist — §5 |
| Contrast gate | **not mine** — design workstream. CI job exists and passes with a notice until the script lands |
| Visual regression | **scaffolded only**, no baselines — §7 |
| Lighthouse | **scaffolded only**, not wired to a workflow — §7 |
| Layer 2 archive smoke build | **not started**. Needs the reference corpus pinned as a submodule or tarball ([007 §2](../specs/007-verification.md)) |
| Zero-JS / storage-disabled / strict-CSP passes | **not started**. All three are Playwright projects; they land with the visual suite |
| URL/alias manifest diff vs the Stack build | **not started** ([010 §2](../specs/010-citizix-migration.md)) |
| Accessibility support statement | **not started** ([007 §4](../specs/007-verification.md)) |

Automated scores are reported as automated scores. A perfect Lighthouse accessibility score is not
WCAG conformance and must never be presented as such.
