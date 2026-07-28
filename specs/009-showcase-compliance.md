# 009 — Hugo Themes showcase compliance

**Status:** verified against live sources
**Date verified:** 2026-07-28
**Supersedes:** issue #1 §5, which described a process that no longer exists

---

## 1. Issue #1 §5 is entirely stale

The original proposal's showcase checklist was written against
[`gohugoio/hugoThemes`](https://github.com/gohugoio/hugoThemes). **That repository is archived.** Its
README now opens with:

> This repository is replaced by https://github.com/gohugoio/hugoThemesSiteBuilder

Everything in §5 that was derived from it is wrong for the current process. Verified against the
live [Hugo contribution docs](https://gohugo.io/contribute/themes/) and the
[hugoThemesSiteBuilder README](https://github.com/gohugoio/hugoThemesSiteBuilder#readme):

| Issue #1 §5 claim | Actual current requirement |
|---|---|
| Submit as a **GitHub issue** — "DO NOT open a pull request!" | **Open a pull request.** Fork the repo, add the theme URL to `themes.txt` in lexicographical order, ensure the Netlify deploy preview succeeds |
| `images/screenshot.png` — **exactly** 1500×1000 px | `images/screenshot.{png,jpg}` — **minimum** 1500×1000, **3:2 aspect ratio** |
| `images/tn.png` — **exactly** 900×600 px | `images/tn.{png,jpg}` — **minimum** 900×600, **3:2 aspect ratio** |
| PNG only | **PNG or JPG** |
| Rebuild 00:00 UTC on the 1st, 4th, 7th … 31st | **Rebuilds daily at 00:00 UTC** |
| Run `./reviewTheme.sh` from `_script/` before submitting | No longer part of the process — the gate is the **Netlify deploy preview** on the PR |
| — *(not mentioned)* | **A root `hugo.toml` with `[module.hugoVersion]` is required** |
| "A demo broken >30 days may be removed without notice" | Not stated in the current README — **do not assert this** |

> **Note on review conflict.** One of the two technical reviews reported §5 as "accurate
> line-for-line". That review checked the archived `hugoThemes` README, whose contents *are* an
> accurate description of a process that is no longer in use. The table above was verified against
> the live contribution docs and the current site-builder README. Where they conflict, the live
> sources govern.

## 2. Current requirements checklist

- [ ] **`theme.toml`** at repo root — **TOML only**, `.yaml`/`.json` rejected. Fields: `name`,
      `license`, `licenselink`, `description`, `homepage`, `tags`, `features`, `min_version`,
      `[author]`.
- [ ] **`hugo.toml`** at repo root with `[module.hugoVersion]` declaring supported versions.
      `extended`, `min` and `max` may be omitted individually. Per
      [ADR-0](006-architecture-decisions.md), Runbook declares `min = "0.146.0"`.
- [ ] **`LICENSE`** — MIT, open source.
- [ ] **`README.md`** with **absolute** URLs only. Relative links break when the README is carried
      onto themes.gohugo.io.
- [ ] **`images/screenshot.png`** — minimum 1500×1000, 3:2 ratio.
- [ ] **`images/tn.png`** — minimum 900×600, 3:2 ratio.
- [ ] **`exampleSite/`** mirroring a Hugo site root, `baseURL = "https://example.com"`. It doubles as
      the synthetic fixture host ([007](007-verification.md) §2).
- [ ] **No third-party tracking with live credentials** anywhere in `exampleSite`.
- [ ] A **public demo site** that builds against latest Hugo.
- [ ] Netlify deploy preview succeeds on the submission PR.
- [ ] Submit: fork `gohugoio/hugoThemesSiteBuilder`, add the theme URL to `themes.txt` in
      lexicographical order, open a PR.

## 3. The demo is exampleSite, not citizix

The showcase demo must be the deployed `exampleSite`, **not citizix.com**. citizix carries AdSense,
GTM and GA4, which the showcase's own "no third-party tracking with live credentials" rule excludes.

This also means the Lighthouse gate runs against the demo, not against production citizix — see
[007](007-verification.md) §3.3.

## 4. Ongoing maintenance obligations

The showcase rebuilds every theme **daily at 00:00 UTC** against latest Hugo. A theme that stops
building disappears from the showcase without any action on the maintainer's part.

Budget for this:

- A **scheduled CI job** building the demo against latest Hugo, independent of pushes, so a Hugo
  release that breaks the theme is discovered by CI rather than by the showcase.
- A stated policy for how quickly latest-Hugo breakage is fixed.

## 5. Also worth shipping for adoption

Not showcase requirements, but expected of a maintained theme:

`CHANGELOG.md` · `CONTRIBUTING.md` · issue templates · security policy · Dependabot for CI actions ·
semantic versioning with immutable tags and release notes · a complete annotated configuration
reference · a migration guide · override examples · an upgrade and deprecation policy ·
`archetypes/default.md` matching the documented front-matter schema · a licence inventory covering
fonts, icons, screenshots and example content, not merely MIT for the theme itself.
