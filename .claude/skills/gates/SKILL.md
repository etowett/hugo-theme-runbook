---
name: gates
description: Build exampleSite the way CI does and run every pull-request gate against it — REQ-CB-1, fixtures, JSON-LD, budgets, links, contrast, agent config, showcase. Use before claiming a change works, before opening a pull request, and whenever a claim in a PR body needs a number behind it. Pass "floor" for the 0.146.0 end of the CI matrix.
argument-hint: "[floor]"
allowed-tools: Bash(hugo *) Bash(python3 *) Bash(git branch*) Bash(env *) Read Grep Glob
---

# Run the gates

Reproduces `.github/workflows/ci.yml` locally. It is about ten seconds on a warm checkout, so
there is no reason to skip it and guess.

`$ARGUMENTS` — if it contains `floor`, build against the **declared minimum** Hugo (0.146.0)
rather than latest. Both ends of the range break independently, which is why CI builds both.

## Environment

```!
hugo version
python3 --version
git branch --show-current
```

## What to run

Work from the repository root. Two spellings are load-bearing:

- **Never `--themesDir ../..`.** It resolves only because a plain checkout sits in a directory
  named after the repository; it fails in a git worktree, a renamed clone and a renamed fork. The
  guardrail hook blocks it.
- **`--destination` must be absolute.** Hugo resolves a relative `--destination` against
  `--source`, so `--source exampleSite --destination public` writes to **`exampleSite/public/`** —
  and then `python3 scripts/check_jsonld.py public` fails with "is not a directory". CI sidesteps
  this by passing `$RUNNER_TEMP/public`. Verified 2026-07-28; the recipe in CONTRIBUTING.md
  "Running the gates" still has the relative form and does not work from the repository root.

### 1 — build, exactly as CI does

```bash
hugo --source exampleSite \
     --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination "$PWD/public" --cleanDestinationDir --gc --minify \
     --panicOnWarning --printPathWarnings
```

`--panicOnWarning` is not optional: Hugo logs a missing layout, a shortcode called with the wrong
arguments and a deprecated function at WARN and then exits 0.

### 2 — every template the build reached

```bash
hugo --source exampleSite \
     --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
     --destination "$PWD/public-unused" --cleanDestinationDir \
     --printUnusedTemplates 2>&1 | tee "$PWD/public-unused.log"
python3 scripts/check_unused_templates.py "$PWD/public-unused.log" \
        .github/unused-templates-allowed.txt
```

A shipped template that nothing reaches is a gap. A deliberate fallback is allowed **only** with a
written reason in the allowlist, and a waiver that has gone stale fails too.

### 3 — the gates

```bash
python3 scripts/check_reqcb1.py                     # builds twice itself and diffs; the strictest one
python3 scripts/check_fixtures.py --check-generated
python3 scripts/check_jsonld.py   public --require-article
python3 scripts/check_budgets.py  public
python3 scripts/check_links.py    public            # internal only; --external is the weekly sweep
python3 scripts/check_contrast.py                   # -v for all 156 ratios
python3 scripts/check_agents.py                     # mirrors, portability, case, stale numbers
python3 scripts/check_showcase.py                   # advisory until M5
python3 .claude/hooks/test_guardrails.py            # only if you touched .claude/hooks/
```

`check_agents.py` needs no build — it reads `.claude/`, `.codex/`, `.agents/` and `.mcp.json`. Run
it after touching any of those, or after changing a number that a doc quotes back. `--fix` repairs
the two mechanical things (the `.agents/skills` symlink, the executable bit on a hook) and reports
everything else, because a mirror disagreement needs a decision rather than a guess.

### 4 — hostile consumer configuration

REQ-CB-1 proves the output does not *change* under forced line numbers. This proves the theme
still *builds* under the other settings a consuming site might force, where output legitimately
differs so an identity diff would be the wrong test.

```bash
for env in \
  "HUGO_MARKUP_HIGHLIGHT_NOCLASSES=true" \
  "HUGO_MARKUP_HIGHLIGHT_GUESSSYNTAX=true" \
  "HUGO_MARKUP_GOLDMARK_RENDERER_UNSAFE=true"
do
  echo "── $env"
  env $env hugo --source exampleSite \
    --themesDir "$(dirname "$PWD")" --theme "$(basename "$PWD")" \
    --destination "$PWD/public-hostile" --cleanDestinationDir --panicOnWarning
done
```

### floor — the other end of the CI matrix

Only when `$ARGUMENTS` contains `floor`. Needs a 0.146.0 binary; if there is not one on this
machine, say so rather than reporting the floor as passing.

```bash
RB_HUGO=/path/to/hugo-0.146.0 python3 scripts/check_reqcb1.py
```

This is the end that catches a template feature which only exists after the floor, and the
`languageCode` / `.Language.LanguageCode` / `.Language.LanguageDirection` deprecation pair whose
replacements do not exist at 0.146.0.

## What not to run

`scripts/check_parity.py` in its diffing mode and `.github/workflows/parity.yml` build a
**private** reference archive. That job is `workflow_dispatch`/`schedule` only, on purpose — a
`pull_request` from a fork gets no secrets, so gating on it would put a red X on every external
contribution. Do not try to make it run locally.

`python3 scripts/check_links.py public --external` hits the network, takes minutes and fails when
a third party's docs site is down. It is a weekly job for that reason.

## Reporting

Report **each gate by name with its result**, not "all gates pass". Where a gate emits a number —
gzipped bytes, contrast assertion count, page count — quote the number, because that is what a
pull-request body needs. If a gate fails, paste its output; do not summarise it away.

Clean up the extra build trees when you are done (`public-unused`, `public-hostile`); they are
already gitignored but they confuse the next run.
