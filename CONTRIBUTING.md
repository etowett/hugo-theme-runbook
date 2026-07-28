# Contributing to Runbook

Thanks for looking. This file is the short version of how the project is built and checked; the long
version is [`docs/verification.md`](docs/verification.md), which explains *why* each gate exists.

**Two things to know before anything else.**

1. **There is no build toolchain, and adding one is a design decision, not a convenience.** Hugo
   assembles the CSS and JavaScript through its own pipeline, and every check is `python3` and the
   standard library. No Node, no npm, no pip install
   ([ADR-1](specs/006-architecture-decisions.md)). A gate that needs a toolchain is a gate
   contributors skip.
2. **Files have owners.** Four workstreams merge in parallel and a cross-boundary edit is a merge
   conflict. See [File ownership](#file-ownership).

## What you need

| | |
|---|---|
| Hugo | any version ≥ 0.146.0. Develop against the latest; CI checks both ends |
| Python | 3.8+ for most scripts. `check_showcase.py` reads TOML, so 3.11+ (`tomllib`) or `tomli` |
| Git | for the submodule install path in the README |

Nothing else. `npx playwright` is needed only for the visual-regression suite, which is not wired
into CI yet.

---

## Building it locally

### The command, and why it is spelled that way

```bash
# from the repository root
hugo --source exampleSite \
     --themesDir "$(dirname "$PWD")" \
     --theme "$(basename "$PWD")" \
     --destination public \
     --cleanDestinationDir --gc --minify \
     --panicOnWarning --printPathWarnings --printUnusedTemplates
```

Development server:

```bash
hugo server --source exampleSite \
            --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
            --disableFastRender
```

**Why not `--themesDir ../..`?** Because `exampleSite/hugo.toml` declares
`theme = "hugo-theme-runbook"`, and Hugo then looks for a **directory of that name** inside
`--themesDir`. On a default GitHub checkout the workspace path already ends in the repository name
(`/home/runner/work/hugo-theme-runbook/hugo-theme-runbook`), so `--themesDir ../..` happens to
resolve — but that is a coincidence of the runner's layout, not a property of the repository. It
breaks in **a git worktree**, in a clone under a different directory name, and in a fork whose
repository was renamed. All three produce `module "hugo-theme-runbook" not found`.

Pairing `--themesDir <parent>` with `--theme <basename>` works everywhere, needs no symlink, and
needs no edit to `exampleSite/hugo.toml` — which belongs to another workstream anyway. The CLI flag
beats the config file. `.github/workflows/ci.yml` derives the same two values from
`$GITHUB_WORKSPACE`.

`--panicOnWarning` is **not optional**. Hugo logs genuinely broken things — a missing layout, a
shortcode called with the wrong arguments, a deprecated function — at WARN level and then exits 0.
Without it, a build that renders nothing useful is a green tick.

### Running the gates

```bash
python3 scripts/check_reqcb1.py                   # builds twice itself and diffs the output
python3 scripts/check_fixtures.py --check-generated
python3 scripts/check_jsonld.py   public
python3 scripts/check_budgets.py  public
python3 scripts/check_links.py    public          # internal only; --external for the weekly sweep
python3 scripts/check_contrast.py                 # add -v to see all 150 ratios
python3 scripts/check_showcase.py                 # advisory
```

Reproducing the CI matrix against the declared floor:

```bash
RB_HUGO=/path/to/hugo-0.146.0 python3 scripts/check_reqcb1.py
```

### Two reproducibility rules that bite

- **`gzip -n -9`, always.** Without `-n`, gzip writes a modification timestamp into the header, byte
  counts move between runs and every budget gate goes flaky.
- **Compare page weights on one platform only.** On the same build, GNU gzip on the Linux runner and
  Apple gzip on macOS disagree — the article p50 reads 2,585 B on CI and 2,728 B locally. A baseline
  captured on a laptop and compared on a runner reports a regression that is really a difference of
  gzip implementation.

---

## File ownership

[`docs/contracts.md`](docs/contracts.md) is the map, and **§0 supersedes §1 for work in flight**.
Two rules:

1. **Do not edit a file another workstream owns.** If you need something changed there, say so in
   your pull-request description and let the owner change it.
2. **Names in the shared contracts are frozen.** Adding is fine; renaming lands in someone else's
   file.

Shared files have explicit seams so they do not become conflicts:

- `assets/css/components.css` and `assets/css/search.css` are already in the concat list in
  `head/css.html`. Nobody edits that list. `with resources.Get` skips a stylesheet that does not
  exist, so an empty one is harmless.
- `i18n/en.yaml` is sectioned. Append inside **your** section.
- `assets/js/runbook.js` is frozen at three modules. Own your module, not the entry point. Search is
  a separate lazy chunk with its own budget.
- `docs/configuration.md` belongs to the release-hygiene stream. **If you add a
  `params.runbook.*` setting, give it a default in the root `hugo.toml`, document it in your own
  doc, and list it in your pull-request body** — it gets folded into the reference from there. A
  setting that exists only in a template is a setting nobody can discover.

---

## Making a change

1. **Branch.** Never commit to `main`.
2. **Add the fixture with the feature, not afterwards.** Synthetic fixtures live in
   `exampleSite/content/` and are what protects a rendering path once the reference archive stops
   exercising it.
3. **Measure rather than assert.** Two of the code block's real bugs — `padding-inline-end` not
   counting toward scrollable overflow, and a `<td>` growing so its inner `<pre>` never gets a width
   to scroll against — were invisible in the markup and were found by driving a browser. If a claim
   in a pull-request body is a number, it should be reproducible from a command in that body.
4. **Run the gates locally.** CI runs them anyway; finding it yourself is faster.
5. **Update the documentation in the same pull request.** A follow-up documentation commit does not
   happen.

### Adding a configuration setting

- Namespace it under `params.runbook.*`. Nothing is read from a bare top-level param, ever, so
  Runbook cannot collide with a consumer's keys.
- Give it a default in the root `hugo.toml` **and** an inline default in
  `_partials/utils/settings.html`.
- **A boolean whose default is `true` is resolved with `isset`, never `| default true`.** `false |
  default true` is `true`, so the obvious spelling silently ignores everyone who turns the feature
  off. Follow the pattern already in that file.
- Every user-visible string it introduces goes in `i18n/en.yaml`, in your section.

### Adding a template

Runbook targets Hugo's post-v0.146.0 template system only. `layouts/_partials/`, `layouts/_markup/`,
`page.html`, `home.html`. **Do not add a legacy `layouts/_default/` path**: when both exist the
legacy one wins, silently ([ADR-0](specs/006-architecture-decisions.md)).

Two version traps the CI matrix exists to catch: Hugo v0.158.0 deprecated `languageCode`,
`.Language.LanguageCode` and `.Language.LanguageDirection`, and their replacements do **not** exist at
the 0.146.0 floor. Use `site.Language.Lang` and a language param for direction — accessors that are
stable across the whole supported range.

---

## Visual regression and the golden-update workflow

**Currently scaffolded, not enabled.** `.github/visual/playwright.config.mjs` pins the environment;
no baselines are committed, deliberately, until the visual freeze. A golden set captured against a
foundation that three workstreams are still changing gets regenerated wholesale on the first real
commit — which teaches everyone that "just re-approve the goldens" is the normal response to a red
diff, and a suite people re-approve reflexively has negative value.

When it is enabled, a screenshot diff has exactly two causes and they need opposite responses, so the
workflow makes the author say which:

1. **Reproduce locally on the same pinned browser.** Never approve from a CI artefact alone — if it
   does not reproduce locally, the diff is environmental and the config is wrong, not the golden.

   ```bash
   npx playwright test --config .github/visual/playwright.config.mjs
   ```

2. **Classify the diff in the pull-request description.** Either *intended* — name the design
   decision — or *unintended*, in which case it is a bug and the golden does not move.

3. **Regenerate only the affected projects.** A blanket `--update-snapshots` hides a second,
   unintended regression inside an intended one.

   ```bash
   npx playwright test --config .github/visual/playwright.config.mjs \
     --project desktop-dark --update-snapshots tests/code-block.spec.mjs
   ```

4. **Commit the new goldens in the same pull request as the change that caused them.** A
   goldens-only commit is unreviewable — the diff is binary and the reason is gone.

5. **Review the images, not the file list.** Approving `+3 -3 baselines/….png` has approved nothing.

6. **A golden update needs the same review as code.** If the only justification is "CI was red", the
   answer is no.

A **font change** is a special case: `└ ├ ─ ●` falling back to another face mid-block is a visual
regression no unit test sees, which is why the `systemctl status` fixture is in the capture set.

---

## Screenshots for the showcase

`images/screenshot.{png,jpg}` (≥ 1500×1000, 3:2) and `images/tn.{png,jpg}` (≥ 900×600, 3:2) are the
last two TODOs in `scripts/check_showcase.py`, and they are **deliberately absent**.

The check is easy to satisfy and the submission is not. A placeholder — or a capture of the current
`exampleSite`, whose home page announces itself as a fixture host and whose posts are called "Code
block smoke test" and "Building the whole stack: 158 code blocks on one page" — would turn the check
green while the actual showcase entry showed a test rig. `specs/008` places screenshots at **M6**,
after the visual freeze and after the demo is deployed, for that reason.

**Do not add a placeholder image to make the check pass.** If you are capturing the real thing:
1500×1000 exactly (3:2, `--force-device-scale-factor=1`), the demo built with `--minify`, an article
page showing code blocks rather than the post list, and both light and dark considered before
choosing.

---

## Pull requests

- One workstream per pull request, matching the ownership map.
- **Say why, not what.** The diff already says what. The body should carry the reasoning, the
  measurements, and anything you tried that did not work.
- Include gate results — budgets in gzipped bytes, contrast assertion count, `--panicOnWarning`
  clean.
- **Name any cross-boundary change you need** rather than making it.
- If a claim cannot be verified from the files, write `TODO(name): confirm …` rather than guessing.

## Reporting things

- **Bugs, features, Hugo-compatibility breaks, accessibility barriers:**
  <https://github.com/etowett/hugo-theme-runbook/issues>, using the templates.
- **Security:** do **not** open a public issue. See [SECURITY.md](SECURITY.md).

## Licence

Contributions are accepted under the [MIT licence](LICENSE) that covers the theme. If you contribute
a font, an icon set or example content that is not your own, its licence goes in the inventory in the
[README](README.md#licences) in the same pull request — the showcase expects the inventory to cover
fonts, icons, screenshots and example content, not merely MIT for the theme.
