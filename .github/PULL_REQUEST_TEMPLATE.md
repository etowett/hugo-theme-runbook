<!--
Say WHY, not what. The diff already says what.

Keep the sections that apply and delete the ones that do not — an unedited template
is worse than a short body. See CONTRIBUTING.md.
-->

## What this changes, and why

<!-- The reasoning. What was wrong, what you decided, and what you rejected on the way.
     If a number appears here it should be reproducible from a command in this body. -->

Closes #

## Ownership

<!-- docs/contracts.md §0 is the current map. Four workstreams merge in parallel and a
     cross-boundary edit is a merge conflict. -->

- Workstream / milestone:
- Files touched are within its ownership: <!-- yes / no + why -->
- **Cross-boundary changes I need but did not make:** <!-- name them; the owner makes them -->

## New or changed configuration

<!-- REQUIRED if you added a params.runbook.* key. It gets folded into
     docs/configuration.md from this list, so an omission here is an undocumented setting. -->

| Key | Type | Default | Effect |
|---|---|---|---|
|  |  |  |  |

- [ ] Default added to the root `hugo.toml`
- [ ] Inline default added to `_partials/utils/settings.html` (`isset`, not `| default true`, for a
      boolean that defaults to `true`)
- [ ] New user-visible strings added to `i18n/en.yaml`, in my section
- [ ] Front-matter keys, if any, match `archetypes/default.md`

## Gates

<!-- Paste real numbers. "Passes" is not a result. -->

| | Result |
|---|---|
| `--panicOnWarning --printPathWarnings --printUnusedTemplates` | |
| Hugo matrix: 0.146.0 non-extended / latest | |
| `check_reqcb1.py` (byte-identical under hostile highlight config) | |
| `check_fixtures.py --check-generated` | |
| `check_jsonld.py` | |
| `check_contrast.py` (assertion count) | |
| `check_budgets.py` — core JS gz / all CSS gz / script tags | |
| `check_links.py` (internal) | |
| `check_showcase.py` | |

## Verification

<!-- What you actually did, not what you intend to. If you drove a browser, say which one,
     at which viewports, with and without scripting. If a claim is untested, say so — the
     accessibility statement's whole value is that it distinguishes the two. -->

- Zero-JavaScript behaviour:
- Both themes:
- Fixture added with the feature:

## Visual diffs

<!-- Only once baselines exist. Every diff must be classified. -->

- [ ] Reproduced locally on the pinned browser (not approved from a CI artefact)
- [ ] Each diff classified as **intended** (name the design decision) or **unintended** (it is a bug;
      the golden does not move)
- [ ] Only the affected projects regenerated — no blanket `--update-snapshots`
- [ ] Goldens committed in this pull request, not a follow-up

## Documentation

- [ ] Updated in this pull request, not a follow-up
- [ ] `CHANGELOG.md` `Unreleased` updated
- [ ] Breaking change? Named here, and the deprecation path is in the changelog

## Anything reviewers should push back on

<!-- Deviations from the spec, shortcuts, things you are unsure about. Naming them gets them
     reviewed; hiding them gets them merged. -->
